"""Shared state-machine engine for the v2 feature APIs (FEAT-038 .. FEAT-048).

Each feature is a FeatureSpec: a set of statuses, an initial status and a list of
Actions. The engine persists items in the product database, enforces tenant
isolation, idempotency (per tenant, feature and Idempotency-Key), revision checks,
transition sources, role gates and per-action checks. Read-only derived fields
come from the spec's ``derive`` hook.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Callable

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

# Session roles (household) plus the legacy header roles that the product API still accepts.
KNOWN_ROLES = frozenset({"owner", "adult", "child", "view_only", "admin", "reviewer", "integrator", "member", "accountant"})
# Children and view-only members can read but not change anything.
WRITE_ROLES = frozenset({"owner", "adult", "admin", "member", "accountant", "reviewer"})
REVIEWER_ROLES = frozenset({"owner", "admin", "accountant", "reviewer"})


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 409, fields: list[str] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = fields or []


def not_found() -> DomainError:
    return DomainError("NOT_FOUND", "Resource not found", 404)


def stale_revision() -> DomainError:
    return DomainError("STALE_REVISION", "Expected revision is stale", 409)


def idempotency_conflict() -> DomainError:
    return DomainError("IDEMPOTENCY_CONFLICT", "Key was used with another payload", 409)


def invalid_transition(action: str, status: str) -> DomainError:
    return DomainError("INVALID_TRANSITION", f"Action '{action}' is not allowed from status {status}", 409)


def validation(messages: list[str], fields: list[str] | None = None) -> DomainError:
    return DomainError("VALIDATION_FAILED", "; ".join(messages), 422, fields)


class CreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(default=0, ge=0)
    client_reference: str = Field(min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)


class CommandRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=0)
    action: str = Field(min_length=1, max_length=64)
    reason: str | None = Field(default=None, max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)


class Hub:
    """Persistence plus cross-feature reads. Shares the product database connection."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.lock = threading.RLock()
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS feature_items(
                 tenant_id TEXT NOT NULL, feature TEXT NOT NULL, item_id TEXT NOT NULL,
                 status TEXT NOT NULL, revision INTEGER NOT NULL, client_reference TEXT NOT NULL,
                 data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                 PRIMARY KEY(tenant_id, feature, item_id))"""
        )
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS feature_idempotency(
                 tenant_id TEXT NOT NULL, feature TEXT NOT NULL, idem_key TEXT NOT NULL,
                 digest TEXT NOT NULL, item_id TEXT NOT NULL,
                 PRIMARY KEY(tenant_id, feature, idem_key))"""
        )
        self.conn.commit()

    # -- feature items -------------------------------------------------------
    def get_item(self, tenant: str, feature: str, item_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM feature_items WHERE tenant_id=? AND feature=? AND item_id=?",
            (tenant, feature, item_id),
        ).fetchone()
        return _item_from_row(row) if row else None

    def list_items(self, tenant: str, feature: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM feature_items WHERE tenant_id=? AND feature=? ORDER BY created_at, item_id",
            (tenant, feature),
        ).fetchall()
        return [_item_from_row(row) for row in rows]

    def save_item(self, tenant: str, feature: str, item: dict[str, Any]) -> None:
        self.conn.execute(
            """INSERT INTO feature_items(tenant_id, feature, item_id, status, revision, client_reference,
                                         data, created_at, updated_at)
               VALUES(?,?,?,?,?,?,?,?,?)
               ON CONFLICT(tenant_id, feature, item_id) DO UPDATE SET
                 status=excluded.status, revision=excluded.revision, data=excluded.data,
                 updated_at=excluded.updated_at""",
            (
                tenant, feature, item["id"], item["status"], item["revision"], item["client_reference"],
                json.dumps(item["data"], ensure_ascii=False, sort_keys=True), item["created_at"], item["updated_at"],
            ),
        )

    # -- idempotency ---------------------------------------------------------
    def idem_lookup(self, tenant: str, feature: str, key: str) -> tuple[str, str] | None:
        row = self.conn.execute(
            "SELECT digest, item_id FROM feature_idempotency WHERE tenant_id=? AND feature=? AND idem_key=?",
            (tenant, feature, key),
        ).fetchone()
        return (row["digest"], row["item_id"]) if row else None

    def idem_save(self, tenant: str, feature: str, key: str, digest: str, item_id: str) -> None:
        self.conn.execute(
            "INSERT INTO feature_idempotency(tenant_id, feature, idem_key, digest, item_id) VALUES(?,?,?,?,?)",
            (tenant, feature, key, digest, item_id),
        )

    # -- cross-feature reads -------------------------------------------------
    def receipt(self, tenant: str, receipt_id: str) -> dict[str, Any] | None:
        """Receipt payload plus status, read from the product receipts table."""
        try:
            row = self.conn.execute(
                "SELECT payload, status FROM receipts WHERE tenant_id=? AND receipt_id=?",
                (tenant, receipt_id),
            ).fetchone()
        except sqlite3.OperationalError:
            return None  # receipts table not created yet (isolated test database)
        if row is None:
            return None
        payload = json.loads(row["payload"])
        return {"status": row["status"], "total": payload.get("total"), "currency": payload.get("currency")}

    def open_quality_tasks(self, tenant: str, period: str | None = None) -> int:
        """Quality tasks still blocking a period. Tasks without a period block every period."""
        count = 0
        for item in self.list_items(tenant, "data_quality"):
            if item["status"] in ("RESOLVED", "EXEMPTED"):
                continue
            task_period = item["data"].get("period")
            if period is None or not task_period or task_period == period:
                count += 1
        return count


def _item_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["item_id"],
        "tenant_id": row["tenant_id"],
        "status": row["status"],
        "revision": row["revision"],
        "client_reference": row["client_reference"],
        "data": json.loads(row["data"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


_hub: Hub | None = None
_hub_lock = threading.Lock()
_resolve_session: Callable[[str], dict[str, Any]] | None = None
_is_production: Callable[[], bool] = lambda: False


def init_hub(
    conn: sqlite3.Connection | None = None,
    *,
    path: str | None = None,
    resolve_session: Callable[[str], dict[str, Any]] | None = None,
    is_production: Callable[[], bool] = lambda: False,
) -> Hub:
    """Bind the feature store to the database. Called once by product_api.

    A file database gets its own connection, so feature writes and product writes do not
    share one sqlite connection (no interleaved transactions); sqlite's locking and the
    busy timeout keep them apart. An in-memory database (tests) uses the connection given.
    resolve_session maps a Bearer token to {tenant_id, role}; it is the only source of
    tenant and role in production.
    """
    global _hub, _resolve_session, _is_production
    if path and path != ":memory:":
        conn = sqlite3.connect(path, check_same_thread=False, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
    if conn is None:
        raise ValueError("init_hub needs a connection or a file path")
    with _hub_lock:
        _hub = Hub(conn)
        _resolve_session = resolve_session
        _is_production = is_production
    return _hub


def hub() -> Hub:
    global _hub
    with _hub_lock:
        if _hub is None:
            conn = sqlite3.connect(":memory:", check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _hub = Hub(conn)
        return _hub


# ---------------------------------------------------------------------------
# Spec model
# ---------------------------------------------------------------------------

# A check returns a list of error messages; an empty list means the action may run.
Check = Callable[[Hub, str, dict[str, Any]], list[str]]
# A target is a fixed status, or a function returning the status for the merged data.
Target = str | Callable[[Hub, str, dict[str, Any]], str]
# Enrich runs before the target and may add derived fields (for example a precheck result).
Enrich = Callable[[Hub, str, dict[str, Any]], None]


@dataclass(frozen=True)
class Action:
    name: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    to: Target
    requires: tuple[str, ...] = ()
    input: str | None = None
    input_type: str = "text"
    input_required: bool = False
    roles: frozenset[str] | None = None
    check: Check | None = None
    enrich: Enrich | None = None


@dataclass(frozen=True)
class FeatureSpec:
    key: str
    prefix: str
    feat: str
    statuses: tuple[str, ...]
    initial: str
    actions: tuple[Action, ...]
    fields: tuple[str, ...]
    numbers: tuple[str, ...] = ()
    create_check: Check | None = None
    derive: Callable[[dict[str, Any]], dict[str, Any]] | None = None

    def action(self, name: str) -> Action | None:
        return next((a for a in self.actions if a.name == name), None)


def _parse_numbers(spec: FeatureSpec, payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    bad: list[str] = []
    for key in spec.numbers:
        if key not in out or out[key] in (None, ""):
            continue
        try:
            value = float(out[key])
        except (TypeError, ValueError):
            bad.append(f"{key} must be a number")
            continue
        if value != value or value in (float("inf"), float("-inf")):
            bad.append(f"{key} must be a finite number")
            continue
        out[key] = round(value, 2)
    if bad:
        raise validation(bad, [m.split(" ")[0] for m in bad])
    return out


def _require_write(role: str) -> None:
    if role not in WRITE_ROLES:
        raise DomainError("FORBIDDEN", f"Role '{role}' is read-only", 403)


def _only(payload: dict[str, Any], allowed: tuple[str, ...]) -> dict[str, Any]:
    """Keep only declared keys so clients cannot write arbitrary fields into item data."""
    return {k: v for k, v in payload.items() if k in allowed}


def _digest(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def _resolve_target(target: Target, hub_: Hub, tenant: str, data: dict[str, Any]) -> str:
    return target(hub_, tenant, data) if callable(target) else target


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip()) or value == ""


class FeatureService:
    def __init__(self, spec: FeatureSpec, store: Hub | Callable[[], Hub]):
        self.spec = spec
        self._store = store

    @property
    def store(self) -> Hub:
        return self._store if isinstance(self._store, Hub) else self._store()

    # -- views ---------------------------------------------------------------
    def view(self, item: dict[str, Any], role: str) -> dict[str, Any]:
        data = dict(item["data"])
        if self.spec.derive:
            data.update(self.spec.derive(data))
        actions: list[dict[str, Any]] = []
        for action in self.spec.actions:
            if item["status"] not in action.sources:
                continue
            if action.roles is not None and role not in action.roles:
                continue
            # Fields the action needs that are not supplied by its own input and are still blank.
            missing = [k for k in action.requires if k != action.input and _is_blank(data.get(k))]
            actions.append({
                "action": action.name,
                "input": action.input,
                "input_type": action.input_type,
                "input_required": action.input_required,
                "missing": missing,
            })
        return {**{k: v for k, v in item.items() if k != "data"}, "data": data, "actions": actions}

    def list(self, tenant: str, role: str) -> list[dict[str, Any]]:
        return [self.view(item, role) for item in self.store.list_items(tenant, self.spec.key)]

    def get(self, tenant: str, role: str, item_id: str) -> dict[str, Any]:
        item = self.store.get_item(tenant, self.spec.key, item_id)
        if item is None:
            raise not_found()
        return self.view(item, role)

    # -- writes --------------------------------------------------------------
    def create(self, tenant: str, role: str, key: str, request: CreateRequest) -> dict[str, Any]:
        _require_write(role)
        digest = _digest("create", request.model_dump_json())
        with self.store.lock:
            prior = self.store.idem_lookup(tenant, self.spec.key, key)
            if prior is not None:
                if prior[0] != digest:
                    raise idempotency_conflict()
                return self.get(tenant, role, prior[1])
            if request.expected_revision != 0:
                raise stale_revision()
            data = _parse_numbers(self.spec, _only(request.payload, self.spec.fields))
            errors: list[str] = []
            if self.spec.create_check:
                errors.extend(self.spec.create_check(self.store, tenant, data))
            if errors:
                raise validation(errors)
            now = datetime.now(UTC).isoformat()
            item = {
                "id": uuid.uuid4().hex,
                "status": self.spec.initial,
                "revision": 0,
                "client_reference": request.client_reference,
                "data": data,
                "created_at": now,
                "updated_at": now,
            }
            with self.store.conn:
                self.store.save_item(tenant, self.spec.key, item)
                self.store.idem_save(tenant, self.spec.key, key, digest, item["id"])
            return self.view(item, role)

    def command(self, tenant: str, role: str, item_id: str, key: str, request: CommandRequest) -> dict[str, Any]:
        _require_write(role)
        digest = _digest("command", item_id, request.model_dump_json())
        with self.store.lock:
            prior = self.store.idem_lookup(tenant, self.spec.key, key)
            if prior is not None:
                if prior[0] != digest:
                    raise idempotency_conflict()
                return self.get(tenant, role, prior[1])
            item = self.store.get_item(tenant, self.spec.key, item_id)
            if item is None:
                raise not_found()
            if request.expected_revision != item["revision"]:
                raise stale_revision()
            action = self.spec.action(request.action)
            if action is None:
                raise DomainError("UNKNOWN_ACTION", f"Unknown action '{request.action}'", 422)
            if action.roles is not None and role not in action.roles:
                raise DomainError("FORBIDDEN", f"Role '{role}' may not run '{action.name}'", 403)
            if item["status"] not in action.sources:
                raise invalid_transition(action.name, item["status"])
            inputs = dict(request.payload)
            if request.reason and "reason" not in inputs:
                inputs["reason"] = request.reason
            payload = _parse_numbers(self.spec, _only(inputs, (action.input,) if action.input else ()))
            if action.input and action.input_required and _is_blank(payload.get(action.input)):
                raise validation([f"{action.input} is required"], [action.input])
            merged = {**item["data"], **payload}
            blank = [k for k in action.requires if _is_blank(merged.get(k))]
            if blank:
                raise validation([f"{k} is required" for k in blank], blank)
            if action.check:
                errors = action.check(self.store, tenant, merged)
                if errors:
                    raise validation(errors)
            if action.enrich:
                action.enrich(self.store, tenant, merged)
            target = _resolve_target(action.to, self.store, tenant, merged)
            if target not in self.spec.statuses:
                raise DomainError("INTERNAL", f"Unknown target status {target}", 500)
            now = datetime.now(UTC).isoformat()
            updated = {
                **item,
                "status": target,
                "revision": item["revision"] + 1,
                "data": merged,
                "updated_at": now,
            }
            with self.store.conn:
                self.store.save_item(tenant, self.spec.key, updated)
                self.store.idem_save(tenant, self.spec.key, key, digest, item_id)
            return self.view(updated, role)


# ---------------------------------------------------------------------------
# HTTP layer
# ---------------------------------------------------------------------------

def _context(authorization: str | None, tenant_id: str | None, role: str | None) -> tuple[str, str]:
    """Tenant and role come from the session. Headers are accepted only outside production (dev, tests)."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if _resolve_session is None:
            raise HTTPException(401, "Session service unavailable")
        try:
            identity = _resolve_session(token)
        except KeyError as exc:
            raise HTTPException(401, "Invalid or expired session") from exc
        return identity["tenant_id"], identity["role"]
    if _is_production():
        raise HTTPException(401, "Session required")
    if not tenant_id or not tenant_id.strip():
        raise HTTPException(401, "Tenant identity is required")
    if role not in KNOWN_ROLES:
        raise HTTPException(403, "Role denied")
    return tenant_id.strip(), role


def _idempotency(value: str | None) -> str:
    if not value or len(value) < 16:
        raise HTTPException(422, "Idempotency-Key must be at least 16 characters")
    return value


def _problem(exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "code": exc.code,
            "message": exc.message,
            "fields": exc.fields,
            "retryable": False,
            "correlation_id": uuid.uuid4().hex,
        },
    )


def make_router(spec: FeatureSpec) -> APIRouter:
    """Build the REST router for one feature: list, create, read, and action (PATCH)."""
    service = FeatureService(spec, hub)
    router = APIRouter(prefix=spec.prefix, tags=[spec.feat])

    @router.get("")
    def list_items(
        authorization: str | None = Header(None, alias="Authorization"),
        x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
        x_role: str | None = Header(None, alias="X-Role"),
    ):
        tenant, role = _context(authorization, x_tenant_id, x_role)
        return {"items": service.list(tenant, role)}

    @router.post("", status_code=201)
    def create_item(
        request: CreateRequest,
        authorization: str | None = Header(None, alias="Authorization"),
        x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
        x_role: str | None = Header(None, alias="X-Role"),
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ):
        tenant, role = _context(authorization, x_tenant_id, x_role)
        try:
            return service.create(tenant, role, _idempotency(idempotency_key), request)
        except DomainError as exc:
            return _problem(exc)

    @router.get("/{item_id}")
    def get_item(
        item_id: str,
        authorization: str | None = Header(None, alias="Authorization"),
        x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
        x_role: str | None = Header(None, alias="X-Role"),
    ):
        tenant, role = _context(authorization, x_tenant_id, x_role)
        try:
            return service.get(tenant, role, item_id)
        except DomainError as exc:
            return _problem(exc)

    @router.patch("/{item_id}")
    def run_action(
        item_id: str,
        request: CommandRequest,
        authorization: str | None = Header(None, alias="Authorization"),
        x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
        x_role: str | None = Header(None, alias="X-Role"),
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ):
        tenant, role = _context(authorization, x_tenant_id, x_role)
        try:
            return service.command(tenant, role, item_id, _idempotency(idempotency_key), request)
        except DomainError as exc:
            return _problem(exc)

    return router

