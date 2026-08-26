"""Application services for the user-facing ReceiptLens product workflows.

The service owns workflow state and tenant isolation. Storage is expressed as a
small SQLite database so jobs, reviews, memberships, connections, and audit
metadata survive process restarts without coupling HTTP handlers to SQL.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ProductConflict(RuntimeError):
    """Raised for stale versions or invalid job state changes."""


@dataclass(frozen=True)
class Actor:
    tenant_id: str
    role: str



# F1.3 — household auth vocabulary (docs/plans/consumer-pivot-2026-08-13.md §3.2).
HOUSEHOLD_ROLES = {"owner", "adult", "child", "view_only"}
WRITE_ROLES = {"owner", "adult"}
LEGACY_HEADER_ROLES = {"admin", "reviewer", "integrator"}
MAGIC_LINK_TTL_SECONDS = 15 * 60
INVITE_TTL_SECONDS = 7 * 24 * 60 * 60
SESSION_TTL_SECONDS = 180 * 24 * 60 * 60


def _sha256(value: str) -> str:
    """SHA-256 hex digest — used to store tokens without keeping the raw secret."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_production() -> bool:
    """True when the deployment is production.

    Reads the environment per call so a test or CLI can flip
    ``RECEIPTLENS_ENV`` after import.  Legacy header auth is only
    honored in non-production environments.
    """
    return os.getenv("RECEIPTLENS_ENV", "").strip().lower() == "production"


class ProductService:
    """Tenant-safe workflow service backed by SQLite."""

    def __init__(self, database: str | Path = ":memory:") -> None:
        self._db = sqlite3.connect(str(database), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._create_schema()

    def _create_schema(self) -> None:
        with self._db:
            self._db.executescript("""
            CREATE TABLE IF NOT EXISTS receipts(
              receipt_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, payload TEXT NOT NULL,
              original_payload TEXT NOT NULL, status TEXT NOT NULL, version INTEGER NOT NULL,
              created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(
              job_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, receipt_id TEXT NOT NULL,
              status TEXT NOT NULL, attempt INTEGER NOT NULL, error TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS members(
              member_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, email TEXT NOT NULL,
              role TEXT NOT NULL, active INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS api_keys(
              key_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL,
              secret_hash TEXT NOT NULL, revoked INTEGER NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS connections(
              connection_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL,
              provider TEXT NOT NULL, mapping TEXT NOT NULL, active INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS exports(
              export_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, connection_id TEXT NOT NULL,
              status TEXT NOT NULL, receipt_ids TEXT NOT NULL, result TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(
              event_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, action TEXT NOT NULL,
              subject_id TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS receipt_metadata(
              receipt_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, tags TEXT NOT NULL,
              project TEXT, cost_center TEXT, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS approval_policies(
              policy_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL,
              threshold REAL NOT NULL, currency TEXT NOT NULL, active INTEGER NOT NULL,
              created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS approvals(
              approval_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, receipt_id TEXT NOT NULL,
              policy_id TEXT NOT NULL, status TEXT NOT NULL, decided_by TEXT,
              note TEXT, created_at TEXT NOT NULL, decided_at TEXT);
            CREATE TABLE IF NOT EXISTS retention_settings(
              tenant_id TEXT PRIMARY KEY, retention_days INTEGER NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS receipt_assets(
              receipt_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, content BLOB NOT NULL,
              content_type TEXT NOT NULL, filename TEXT NOT NULL, sha256 TEXT NOT NULL,
              boxes TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS activity_history(
              history_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, subject_id TEXT NOT NULL,
              action TEXT NOT NULL, before_json TEXT, after_json TEXT,
              actor_role TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS auth_tokens(
              token_hash TEXT PRIMARY KEY, email TEXT NOT NULL, purpose TEXT NOT NULL,
              tenant_id TEXT, role TEXT, invite_id TEXT,
              expires_at TEXT NOT NULL, consumed_at TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS household_invites(
              invite_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, email TEXT NOT NULL,
              role TEXT NOT NULL, invited_by TEXT NOT NULL, status TEXT NOT NULL,
              token_hash TEXT, created_at TEXT NOT NULL, accepted_at TEXT);
            CREATE TABLE IF NOT EXISTS sessions(
              session_token TEXT PRIMARY KEY, email TEXT NOT NULL, tenant_id TEXT NOT NULL,
              role TEXT NOT NULL, expires_at TEXT NOT NULL, created_at TEXT NOT NULL,
              display_name TEXT);
            """)
            # Migration for existing DBs that were created before display_name
            try:
                cols = {r[1] for r in self._db.execute("PRAGMA table_info(sessions)").fetchall()}
                if "display_name" not in cols:
                    self._db.execute("ALTER TABLE sessions ADD COLUMN display_name TEXT")
                    self._db.commit()
            except Exception:
                pass

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _audit(self, tenant: str, action: str, subject: str | None = None) -> None:
        self._db.execute("INSERT INTO audit VALUES(?,?,?,?,?)", (str(uuid.uuid4()), tenant, action, subject, self._now()))

    @staticmethod
    def _receipt_payload(receipt: Any) -> dict[str, Any]:
        return {
            "vendor": receipt.merchant, "date": receipt.date, "total": receipt.total,
            "tax": receipt.tax, "currency": receipt.currency,
            "line_items": [
                {"name": i.name, "price": i.price, "category": getattr(i, "category", None)}
                for i in receipt.items
            ],
            "confidence": dict(receipt.confidence),
            "confidence_level": getattr(receipt, "confidence_level", None),
        }

    def create_receipt(self, actor: Actor, parsed: Any, filename: str) -> dict[str, Any]:
        payload = self._receipt_payload(parsed)
        confidences = [v for v in payload["confidence"].values() if isinstance(v, (int, float))]
        status = "needs_review" if not confidences or min(confidences) < 0.7 else "completed"
        receipt_id, job_id, now = str(uuid.uuid4()), str(uuid.uuid4()), self._now()
        with self._lock, self._db:
            encoded = json.dumps(payload, sort_keys=True)
            self._db.execute("INSERT INTO receipts VALUES(?,?,?,?,?,?,?)", (receipt_id, actor.tenant_id, encoded, encoded, status, 1, now))
            self._db.execute("INSERT INTO jobs VALUES(?,?,?,?,?,?,?)", (job_id, actor.tenant_id, receipt_id, status, 1, None, now))
            self._audit(actor.tenant_id, "receipt.created", receipt_id)
        return {"receipt_id": receipt_id, "job_id": job_id, "status": status, "filename": filename, "receipt": payload}

    def list_jobs(self, actor: Actor) -> list[dict[str, Any]]:
        rows = self._db.execute("SELECT * FROM jobs WHERE tenant_id=? ORDER BY created_at DESC", (actor.tenant_id,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _review_row_matches(
        row: Any, payload: dict[str, Any], confidence: dict[str, Any],
        confidence_field: str | None, confidence_lt: float | None,
        readiness: str | None,
    ) -> bool:
        if readiness and row["status"] != readiness:
            return False
        value = confidence.get(confidence_field) if confidence_field else None
        return not (confidence_lt is not None and value is not None and float(value) >= confidence_lt)

    def list_reviews(self, actor: Actor, confidence_field: str | None = None,
                     confidence_lt: float | None = None, readiness: str | None = None,
                     sort: str = "created_asc", limit: int = 50, offset: int = 0) -> dict[str, Any]:
        allowed_fields = {"vendor", "date", "total", "tax", "currency", "line_items"}
        if confidence_field is not None and confidence_field not in allowed_fields:
            raise ValueError("unsupported confidence field")
        if confidence_lt is not None and not 0 <= confidence_lt <= 1:
            raise ValueError("confidence_lt must be between 0 and 1")
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError("invalid pagination")
        rows = self._db.execute("SELECT * FROM receipts WHERE tenant_id=? ORDER BY created_at", (actor.tenant_id,)).fetchall()
        items=[]
        for row in rows:
            payload=json.loads(row["payload"]); confidence=payload.get("confidence") or {}
            value=confidence.get(confidence_field) if confidence_field else None
            if not self._review_row_matches(row, payload, confidence, confidence_field, confidence_lt, readiness):
                continue
            items.append({"receipt_id":row["receipt_id"],"status":row["status"],"readiness":row["status"],
                          "version":row["version"],"receipt":payload,"lowest_confidence":min([v for v in confidence.values() if isinstance(v,(int,float))],default=None),
                          "selected_confidence":value,"created_at":row["created_at"]})
        if sort == "amount_desc": items.sort(key=lambda x: float(x["receipt"].get("total") or 0), reverse=True)
        elif sort == "confidence_asc": items.sort(key=lambda x: (-1 if x["selected_confidence"] is None else x["selected_confidence"]))
        elif sort != "created_asc": raise ValueError("unsupported sort")
        return {"items":items[offset:offset+limit],"total":len(items),"limit":limit,"offset":offset}

    def correct(self, actor: Actor, receipt_id: str, changes: dict[str, Any], expected_version: int, complete: bool) -> dict[str, Any]:
        if not self.can_write(actor):
            raise PermissionError("read-only household role")
        with self._lock, self._db:
            row = self._db.execute("SELECT * FROM receipts WHERE tenant_id=? AND receipt_id=?", (actor.tenant_id, receipt_id)).fetchone()
            if not row: raise KeyError(receipt_id)
            if row["version"] != expected_version: raise ProductConflict("stale receipt version")
            allowed = {"vendor", "date", "total", "tax", "currency", "line_items"}
            if not changes or set(changes) - allowed: raise ValueError("unsupported or empty correction")
            payload = json.loads(row["payload"]); payload.update(changes)
            status = "completed" if complete else "needs_review"; version = expected_version + 1
            self._db.execute("UPDATE receipts SET payload=?,status=?,version=? WHERE receipt_id=?", (json.dumps(payload, sort_keys=True), status, version, receipt_id))
            self._db.execute("UPDATE jobs SET status=? WHERE tenant_id=? AND receipt_id=?", (status, actor.tenant_id, receipt_id))
            self._audit(actor.tenant_id, "receipt.corrected", receipt_id)
            return {"receipt_id": receipt_id, "status": status, "version": version, "receipt": payload}

    def retry(self, actor: Actor, job_id: str) -> dict[str, Any]:
        with self._lock, self._db:
            row = self._db.execute("SELECT * FROM jobs WHERE tenant_id=? AND job_id=?", (actor.tenant_id, job_id)).fetchone()
            if not row: raise KeyError(job_id)
            attempt = row["attempt"] + 1
            self._db.execute("UPDATE jobs SET attempt=?,error=NULL WHERE job_id=?", (attempt, job_id))
            self._audit(actor.tenant_id, "job.retried", job_id)
            return {**dict(row), "attempt": attempt, "retried": True}

    def cancel(self, actor: Actor, job_id: str) -> dict[str, Any]:
        with self._lock, self._db:
            row = self._db.execute("SELECT * FROM jobs WHERE tenant_id=? AND job_id=?", (actor.tenant_id, job_id)).fetchone()
            if not row: raise KeyError(job_id)
            if row["status"] in {"completed", "needs_review", "failed", "cancelled"}: raise ProductConflict("job is not cancellable")
            self._db.execute("UPDATE jobs SET status='cancelled' WHERE job_id=?", (job_id,))
            self._audit(actor.tenant_id, "job.cancelled", job_id)
            return {"job_id": job_id, "status": "cancelled"}

    def add_member(self, actor: Actor, email: str, role: str) -> dict[str, Any]:
        if not self.can_manage_household(actor): raise PermissionError
        if role not in {"admin", "reviewer", "integrator", *HOUSEHOLD_ROLES}: raise ValueError("invalid role")
        member_id = str(uuid.uuid4())
        with self._db:
            self._db.execute("INSERT INTO members VALUES(?,?,?,?,1)", (member_id, actor.tenant_id, email.lower(), role))
            self._audit(actor.tenant_id, "member.created", member_id)
        return {"member_id": member_id, "email": email.lower(), "role": role, "active": True}

    def list_members(self, actor: Actor) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT member_id,email,role,active FROM members WHERE tenant_id=? ORDER BY email",
            (actor.tenant_id,),
        ).fetchall()
        return [{**dict(row), "active": bool(row["active"])} for row in rows]

    def list_connections(self, actor: Actor) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT connection_id,name,provider,mapping,active FROM connections "
            "WHERE tenant_id=? ORDER BY name", (actor.tenant_id,),
        ).fetchall()
        return [{**dict(row), "mapping": json.loads(row["mapping"]),
                 "active": bool(row["active"])} for row in rows]

    def list_approvals(self, actor: Actor, status: str | None = None) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT a.*,p.name AS policy_name,r.payload,m.project,m.cost_center "
            "FROM approvals a JOIN approval_policies p ON p.policy_id=a.policy_id "
            "JOIN receipts r ON r.receipt_id=a.receipt_id "
            "LEFT JOIN receipt_metadata m ON m.receipt_id=a.receipt_id "
            "WHERE a.tenant_id=? ORDER BY a.created_at DESC", (actor.tenant_id,),
        ).fetchall()
        items = []
        for row in rows:
            if status and row["status"] != status:
                continue
            payload = json.loads(row["payload"])
            items.append({
                "approval_id": row["approval_id"], "receipt_id": row["receipt_id"],
                "policy_id": row["policy_id"], "policy_name": row["policy_name"],
                "status": row["status"], "decided_by": row["decided_by"],
                "note": row["note"], "created_at": row["created_at"],
                "decided_at": row["decided_at"], "vendor": payload.get("vendor"),
                "total": payload.get("total"), "currency": payload.get("currency"),
                "project": row["project"], "cost_center": row["cost_center"],
            })
        return items

    def retention_days(self, actor: Actor) -> int:
        row = self._db.execute(
            "SELECT retention_days FROM retention_settings WHERE tenant_id=?",
            (actor.tenant_id,),
        ).fetchone()
        return int(row[0]) if row else 30

    def create_api_key(self, actor: Actor, name: str) -> dict[str, Any]:
        if actor.role != "admin": raise PermissionError
        key_id, secret = str(uuid.uuid4()), "rl_" + secrets.token_urlsafe(24)
        digest = hashlib.sha256(secret.encode()).hexdigest()
        with self._db:
            self._db.execute("INSERT INTO api_keys VALUES(?,?,?,?,0,?)", (key_id, actor.tenant_id, name, digest, self._now()))
            self._audit(actor.tenant_id, "api_key.created", key_id)
        return {"key_id": key_id, "name": name, "secret": secret}

    def create_connection(self, actor: Actor, name: str, provider: str, mapping: dict[str, str]) -> dict[str, Any]:
        if provider not in {"csv", "quickbooks", "xero"}: raise ValueError("unsupported provider")
        required = {"vendor", "total", "currency"}
        if not required.issubset(mapping): raise ValueError("mapping requires vendor, total and currency")
        cid = str(uuid.uuid4())
        with self._db:
            self._db.execute("INSERT INTO connections VALUES(?,?,?,?,?,1)", (cid, actor.tenant_id, name, provider, json.dumps(mapping, sort_keys=True)))
            self._audit(actor.tenant_id, "connection.created", cid)
        return {"connection_id": cid, "name": name, "provider": provider, "mapping": mapping, "active": True}

    def test_connection(self, actor: Actor, connection_id: str) -> dict[str, Any]:
        row = self._db.execute("SELECT * FROM connections WHERE tenant_id=? AND connection_id=? AND active=1", (actor.tenant_id, connection_id)).fetchone()
        if not row: raise KeyError(connection_id)
        return {"connection_id": connection_id, "status": "ok", "provider": row["provider"]}

    def export(self, actor: Actor, connection_id: str, receipt_ids: list[str]) -> dict[str, Any]:
        connection = self._db.execute("SELECT * FROM connections WHERE tenant_id=? AND connection_id=?", (actor.tenant_id, connection_id)).fetchone()
        if not connection: raise KeyError(connection_id)
        rows=[]
        for rid in receipt_ids:
            row=self._db.execute("SELECT payload FROM receipts WHERE tenant_id=? AND receipt_id=? AND status='completed'", (actor.tenant_id,rid)).fetchone()
            if row: rows.append(json.loads(row["payload"]))
        export_id=str(uuid.uuid4()); result={"exported":len(rows),"requested":len(receipt_ids)}
        with self._db:
            self._db.execute("INSERT INTO exports VALUES(?,?,?,?,?,?,?)", (export_id,actor.tenant_id,connection_id,"completed",json.dumps(receipt_ids),json.dumps(result),self._now()))
            self._audit(actor.tenant_id,"export.completed",export_id)
        return {"export_id":export_id,"status":"completed",**result}

    @staticmethod
    def receipt_readiness(payload: dict[str, Any], status: str,
                          cost_center: str | None) -> dict[str, Any]:
        """Return early accounting readiness for list and work-queue visibility."""
        issues: list[dict[str, str]] = []
        required = {
            "vendor": "Add a merchant before export.",
            "date": "Add a receipt date before export.",
            "total": "Add a total before export.",
            "currency": "Add a currency before export.",
        }
        for field, message in required.items():
            if payload.get(field) in (None, ""):
                issues.append({"code": f"missing_{field}", "field": field,
                               "severity": "blocker", "message": message})
        total = payload.get("total")
        tax = payload.get("tax")
        if total is not None and float(total) < 0:
            issues.append({"code": "negative_total", "field": "total",
                           "severity": "blocker", "message": "Total cannot be negative."})
        if tax is not None and total is not None and float(tax) > float(total):
            issues.append({"code": "tax_exceeds_total", "field": "tax",
                           "severity": "blocker", "message": "Tax cannot exceed total."})
        if not cost_center:
            issues.append({"code": "missing_cost_center", "field": "cost_center",
                           "severity": "blocker", "message": "Select a cost center before export."})
        if status != "completed":
            issues.append({"code": "review_incomplete", "field": "status",
                           "severity": "blocker", "message": "Complete receipt review before export."})
        blocker_count = sum(issue["severity"] == "blocker" for issue in issues)
        warning_count = sum(issue["severity"] == "warning" for issue in issues)
        state = "blocked" if blocker_count else ("warning" if warning_count else "exportable")
        return {"state": state, "blocker_count": blocker_count,
                "warning_count": warning_count, "issues": issues}

    @staticmethod
    def _search_row_matches(
        row: Any, payload: dict[str, Any], tags: list[Any],
        readiness_state: str, query: str | None, status: str | None,
        tag: str | None, min_total: float | None, max_total: float | None,
        readiness: str | None,
    ) -> bool:
        total = payload.get("total")
        haystack = " ".join(str(payload.get(k) or "") for k in ("vendor", "date", "currency")).lower()
        if query and query.lower() not in haystack:
            return False
        if status and row["status"] != status:
            return False
        if tag and tag.lower() not in {str(x).lower() for x in tags}:
            return False
        if min_total is not None and (total is None or float(total) < min_total):
            return False
        if max_total is not None and (total is None or float(total) > max_total):
            return False
        return not (readiness and readiness_state != readiness)

    def search_receipts(self, actor: Actor, query: str | None = None,
                        status: str | None = None, tag: str | None = None,
                        min_total: float | None = None, max_total: float | None = None,
                        limit: int = 50, offset: int = 0,
                        readiness: str | None = None) -> dict[str, Any]:
        """Search tenant receipts with stable pagination and early readiness."""
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError("limit must be 1..200 and offset must be non-negative")
        if readiness not in {None, "", "blocked", "warning", "exportable"}:
            raise ValueError("unsupported readiness filter")
        rows = self._db.execute(
            "SELECT r.*,m.tags,m.project,m.cost_center FROM receipts r "
            "LEFT JOIN receipt_metadata m ON m.receipt_id=r.receipt_id "
            "WHERE r.tenant_id=? ORDER BY r.created_at DESC, r.receipt_id", (actor.tenant_id,)
        ).fetchall()
        items=[]
        for row in rows:
            payload=json.loads(row["payload"])
            tags=json.loads(row["tags"] or "[]")
            result_readiness = self.receipt_readiness(payload, row["status"], row["cost_center"])
            if not self._search_row_matches(
                row, payload, tags, result_readiness["state"], query, status,
                tag, min_total, max_total, readiness,
            ):
                continue
            items.append({"receipt_id":row["receipt_id"],"status":row["status"],
                          "version":row["version"],"created_at":row["created_at"],
                          "receipt":payload,"metadata":{"tags":tags,"project":row["project"],
                          "cost_center":row["cost_center"]}, "readiness": result_readiness})
        return {"items":items[offset:offset+limit],"total":len(items),"limit":limit,"offset":offset}

    def get_receipt(self, actor: Actor, receipt_id: str) -> dict[str, Any]:
        """Return one tenant receipt in the same shape as search_receipts items."""
        row = self._db.execute(
            "SELECT r.*,m.tags,m.project,m.cost_center FROM receipts r "
            "LEFT JOIN receipt_metadata m ON m.receipt_id=r.receipt_id "
            "WHERE r.tenant_id=? AND r.receipt_id=?", (actor.tenant_id, receipt_id)
        ).fetchone()
        if not row: raise KeyError(receipt_id)
        payload = json.loads(row["payload"])
        tags = json.loads(row["tags"] or "[]")
        return {
            "receipt_id": row["receipt_id"], "status": row["status"],
            "version": row["version"], "created_at": row["created_at"],
            "receipt": payload,
            "metadata": {"tags": tags, "project": row["project"],
                         "cost_center": row["cost_center"]},
            "readiness": self.receipt_readiness(payload, row["status"],
                                                row["cost_center"]),
        }

    def set_metadata(self, actor: Actor, receipt_id: str, tags: list[str],
                     project: str | None, cost_center: str | None) -> dict[str, Any]:
        """Attach normalized tags and allocation metadata to a tenant receipt."""
        row=self._db.execute("SELECT 1 FROM receipts WHERE tenant_id=? AND receipt_id=?",
                             (actor.tenant_id,receipt_id)).fetchone()
        if not row: raise KeyError(receipt_id)
        deduped: dict[str, str] = {}
        for tag_value in tags:
            cleaned = tag_value.strip()
            if cleaned:
                deduped.setdefault(cleaned.lower(), cleaned)
        normalized=sorted(deduped.values(), key=str.lower)
        if len(normalized)>20 or any(len(t)>40 for t in normalized):
            raise ValueError("at most 20 tags of 40 characters are allowed")
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO receipt_metadata VALUES(?,?,?,?,?,?)",
                (receipt_id,actor.tenant_id,json.dumps(normalized),project,cost_center,self._now()))
            self._audit(actor.tenant_id,"receipt.metadata.updated",receipt_id)
        return {"receipt_id":receipt_id,"tags":normalized,"project":project,"cost_center":cost_center}

    def create_approval_policy(self, actor: Actor, name: str, threshold: float,
                               currency: str = "USD") -> dict[str, Any]:
        if actor.role != "admin": raise PermissionError
        if threshold <= 0: raise ValueError("threshold must be positive")
        pid=str(uuid.uuid4())
        with self._db:
            self._db.execute("INSERT INTO approval_policies VALUES(?,?,?,?,?,1,?)",
                (pid,actor.tenant_id,name,threshold,currency.upper(),self._now()))
            self._audit(actor.tenant_id,"approval_policy.created",pid)
        return {"policy_id":pid,"name":name,"threshold":threshold,
                "currency":currency.upper(),"active":True}

    def request_approval(self, actor: Actor, receipt_id: str) -> dict[str, Any]:
        row=self._db.execute("SELECT payload FROM receipts WHERE tenant_id=? AND receipt_id=?",
                             (actor.tenant_id,receipt_id)).fetchone()
        if not row: raise KeyError(receipt_id)
        payload=json.loads(row["payload"]); total=payload.get("total"); currency=payload.get("currency")
        policy=self._db.execute("SELECT * FROM approval_policies WHERE tenant_id=? AND active=1 "
            "AND currency=? AND threshold<=? ORDER BY threshold DESC LIMIT 1",
            (actor.tenant_id,currency,float(total or 0))).fetchone()
        if not policy: return {"receipt_id":receipt_id,"required":False,"status":"not_required"}
        existing=self._db.execute("SELECT * FROM approvals WHERE tenant_id=? AND receipt_id=? AND status='pending'",
                                  (actor.tenant_id,receipt_id)).fetchone()
        if existing: return {**dict(existing),"required":True}
        aid=str(uuid.uuid4()); now=self._now()
        with self._db:
            self._db.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,?)",
                (aid,actor.tenant_id,receipt_id,policy["policy_id"],"pending",None,None,now,None))
            self._audit(actor.tenant_id,"approval.requested",aid)
        return {"approval_id":aid,"receipt_id":receipt_id,"policy_id":policy["policy_id"],
                "required":True,"status":"pending","created_at":now}

    def decide_approval(self, actor: Actor, approval_id: str, decision: str,
                        note: str | None = None) -> dict[str, Any]:
        if actor.role not in {"admin","reviewer"}: raise PermissionError
        if decision not in {"approved","rejected"}: raise ValueError("invalid decision")
        row=self._db.execute("SELECT * FROM approvals WHERE tenant_id=? AND approval_id=?",
                             (actor.tenant_id,approval_id)).fetchone()
        if not row: raise KeyError(approval_id)
        if row["status"] != "pending": raise ProductConflict("approval already decided")
        now=self._now()
        with self._db:
            self._db.execute("UPDATE approvals SET status=?,decided_by=?,note=?,decided_at=? WHERE approval_id=?",
                (decision,actor.role,note,now,approval_id))
            self._audit(actor.tenant_id,"approval."+decision,approval_id)
        return {"approval_id":approval_id,"receipt_id":row["receipt_id"],"status":decision,
                "note":note,"decided_at":now}

    def set_retention(self, actor: Actor, retention_days: int) -> dict[str, Any]:
        if actor.role != "admin": raise PermissionError
        if not 1 <= retention_days <= 3650: raise ValueError("retention_days must be 1..3650")
        with self._db:
            self._db.execute("INSERT OR REPLACE INTO retention_settings VALUES(?,?,?)",
                             (actor.tenant_id,retention_days,self._now()))
            self._audit(actor.tenant_id,"retention.updated",actor.tenant_id)
        return {"retention_days":retention_days}

    def purge_expired(self, actor: Actor, now: datetime | None = None) -> dict[str, Any]:
        if actor.role != "admin": raise PermissionError
        setting=self._db.execute("SELECT retention_days FROM retention_settings WHERE tenant_id=?",
                                 (actor.tenant_id,)).fetchone()
        days=setting[0] if setting else 30
        current=now or datetime.now(UTC)
        from datetime import timedelta
        cutoff=(current-timedelta(days=days)).isoformat()
        rows=self._db.execute("SELECT receipt_id FROM receipts WHERE tenant_id=? AND created_at<?",
                              (actor.tenant_id,cutoff)).fetchall()
        ids=[r[0] for r in rows]
        with self._db:
            for rid in ids:
                self._db.execute("DELETE FROM receipt_metadata WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid))
                self._db.execute("DELETE FROM receipt_assets WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid))
                self._db.execute("DELETE FROM activity_history WHERE tenant_id=? AND subject_id=?",(actor.tenant_id,rid))
                self._db.execute("DELETE FROM approvals WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid))
                self._db.execute("DELETE FROM jobs WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid))
                self._db.execute("DELETE FROM receipts WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid))
            self._audit(actor.tenant_id,"retention.purged",str(len(ids)))
        return {"purged":len(ids),"retention_days":days,"cutoff":cutoff}

    def portability_export(self, actor: Actor) -> dict[str, Any]:
        """Return a deterministic, tenant-scoped machine-readable data export."""
        receipts=self.search_receipts(actor,limit=200)["items"]
        approvals=[dict(r) for r in self._db.execute(
            "SELECT approval_id,receipt_id,policy_id,status,decided_by,note,created_at,decided_at "
            "FROM approvals WHERE tenant_id=? ORDER BY created_at",(actor.tenant_id,)).fetchall()]
        self._audit(actor.tenant_id,"portability.exported",actor.tenant_id)
        return {"schema_version":1,"tenant_id":actor.tenant_id,"exported_at":self._now(),
                "receipts":receipts,"approvals":approvals}

    @staticmethod
    def _clean_line_items(line_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate and normalize line items; raises ValueError on the first bad item."""
        clean_items = []
        for index, item in enumerate(line_items):
            name = str(item.get("name") or "").strip()
            try:
                quantity = float(item.get("quantity", 1))
                unit_price = float(item.get("unit_price", item.get("price", 0)))
                amount = float(item.get("amount", quantity * unit_price))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"invalid line item at index {index}") from exc
            if not name or quantity <= 0 or unit_price < 0 or amount < 0:
                raise ValueError(f"invalid line item at index {index}")
            clean_items.append({
                "name": name, "quantity": quantity, "unit_price": unit_price,
                "amount": round(amount, 2), "tax_rate": item.get("tax_rate"),
                "category": item.get("category"),
            })
        return clean_items

    @staticmethod
    def _clean_workspace_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        """Validate and normalize tags/project/cost_center; raises ValueError on bad tags."""
        tags = metadata.get("tags") or []
        normalized: dict[str, str] = {}
        for value in tags:
            cleaned = str(value).strip()
            if cleaned:
                normalized.setdefault(cleaned.lower(), cleaned)
        tag_values = sorted(normalized.values(), key=str.lower)
        if len(tag_values) > 20 or any(len(tag) > 40 for tag in tag_values):
            raise ValueError("at most 20 tags of 40 characters are allowed")
        return {
            "tags": tag_values,
            "project": str(metadata.get("project") or "").strip() or None,
            "cost_center": str(metadata.get("cost_center") or "").strip() or None,
        }

    def _receipt_row(self, actor: Actor, receipt_id: str) -> Any:
        """Fetch one tenant receipt or raise KeyError."""
        row = self._db.execute(
            "SELECT * FROM receipts WHERE tenant_id=? AND receipt_id=?",
            (actor.tenant_id, receipt_id),
        ).fetchone()
        if not row:
            raise KeyError(receipt_id)
        return row

    def _apply_workspace_tx(
        self, actor: Actor, receipt_id: str, expected_version: int,
        fields: dict[str, Any], clean_items: list[dict[str, Any]] | None,
        clean_metadata: dict[str, Any] | None, complete: bool,
    ) -> tuple[str, int, dict[str, Any]]:
        """Apply the workspace update inside the transaction.

        Returns (status, version, payload). Raises KeyError/ProductConflict on
        stale or missing receipts.
        """
        row = self._receipt_row(actor, receipt_id)
        if row["version"] != expected_version:
            raise ProductConflict("stale receipt version")
        payload = json.loads(row["payload"])
        payload.update(fields)
        if clean_items is not None:
            payload["line_items"] = clean_items
        status = "completed" if complete else row["status"]
        version = expected_version + 1
        self._db.execute(
            "UPDATE receipts SET payload=?,status=?,version=? WHERE tenant_id=? AND receipt_id=?",
            (json.dumps(payload, sort_keys=True), status, version, actor.tenant_id, receipt_id),
        )
        self._db.execute(
            "UPDATE jobs SET status=? WHERE tenant_id=? AND receipt_id=?",
            (status, actor.tenant_id, receipt_id),
        )
        if clean_metadata is not None:
            self._db.execute(
                "INSERT OR REPLACE INTO receipt_metadata VALUES(?,?,?,?,?,?)",
                (receipt_id, actor.tenant_id, json.dumps(clean_metadata["tags"]),
                 clean_metadata["project"], clean_metadata["cost_center"], self._now()),
            )
        self._audit(actor.tenant_id, "receipt.workspace.updated", receipt_id)
        return status, version, payload

    def _read_workspace_metadata(self, actor: Actor, receipt_id: str) -> dict[str, Any]:
        """Read stored metadata back after the transaction commits."""
        metadata_row = self._db.execute(
            "SELECT tags,project,cost_center FROM receipt_metadata WHERE tenant_id=? AND receipt_id=?",
            (actor.tenant_id, receipt_id),
        ).fetchone()
        return {
            "tags": json.loads(metadata_row["tags"]) if metadata_row else [],
            "project": metadata_row["project"] if metadata_row else None,
            "cost_center": metadata_row["cost_center"] if metadata_row else None,
        }

    def update_receipt_workspace(
        self, actor: Actor, receipt_id: str, expected_version: int,
        fields: dict[str, Any] | None, line_items: list[dict[str, Any]] | None,
        metadata: dict[str, Any] | None, complete: bool,
    ) -> dict[str, Any]:
        """Atomically update review fields, line items and accounting metadata.

        All validation happens before the transaction so users never receive a
        partially saved receipt when one section is invalid.
        """
        if not self.can_write(actor):
            raise PermissionError("write role required (owner/adult)")
        allowed = {"vendor", "date", "total", "tax", "currency"}
        fields = dict(fields or {})
        if set(fields) - allowed:
            raise ValueError("unsupported receipt field")
        if not fields and line_items is None and metadata is None:
            raise ValueError("at least one workspace change is required")

        clean_items = self._clean_line_items(line_items) if line_items is not None else None
        clean_metadata = self._clean_workspace_metadata(metadata) if metadata is not None else None

        with self._lock, self._db:
            status, version, payload = self._apply_workspace_tx(
                actor, receipt_id, expected_version, fields,
                clean_items, clean_metadata, complete,
            )

        result_metadata = self._read_workspace_metadata(actor, receipt_id)
        return {"receipt_id": receipt_id, "status": status, "version": version,
                "receipt": payload, "metadata": result_metadata}

    def work_queue(self, actor: Actor, limit: int = 100) -> dict[str, Any]:
        """Return a deterministic, role-aware queue of actionable daily work."""
        if not 1 <= limit <= 200:
            raise ValueError("limit must be 1..200")
        items: list[dict[str, Any]] = []
        failed = self._db.execute(
            "SELECT job_id,receipt_id,error,created_at FROM jobs "
            "WHERE tenant_id=? AND status='failed'", (actor.tenant_id,),
        ).fetchall()
        for row in failed:
            items.append({
                "task_id": "failed:" + row["job_id"], "type": "failed_job",
                "priority": 10, "receipt_id": row["receipt_id"], "subject_id": row["job_id"],
                "title": "Feldolgozási hiba",
                "reason": row["error"] or "A nyugta feldolgozása sikertelen.",
                "action_label": "Újrapróbálás", "action_url": "#upload",
                "created_at": row["created_at"],
            })
        reviews = self._db.execute(
            "SELECT receipt_id,payload,created_at FROM receipts "
            "WHERE tenant_id=? AND status='needs_review'", (actor.tenant_id,),
        ).fetchall()
        for row in reviews:
            payload = json.loads(row["payload"])
            rid = row["receipt_id"]
            items.append({
                "task_id": "review:" + rid, "type": "review",
                "priority": 20, "receipt_id": rid, "subject_id": rid,
                "title": payload.get("vendor") or "Ellenőrzendő nyugta",
                "reason": "Egy vagy több OCR-mező bizonyossága alacsony.",
                "action_label": "Ellenőrzés", "action_url": f"#review?receipt={rid}",
                "created_at": row["created_at"],
            })
        blocker_rows = self._db.execute(
            "SELECT r.receipt_id,r.payload,r.status,r.created_at,m.cost_center FROM receipts r "
            "LEFT JOIN receipt_metadata m ON m.receipt_id=r.receipt_id "
            "WHERE r.tenant_id=? AND r.status='completed'", (actor.tenant_id,),
        ).fetchall()
        for row in blocker_rows:
            readiness = self.receipt_readiness(json.loads(row["payload"]), row["status"], row["cost_center"])
            if readiness["state"] != "blocked":
                continue
            first = readiness["issues"][0]
            receipt_id = row["receipt_id"]
            field = first["field"]
            items.append({
                "task_id": "export-blocker:" + receipt_id, "type": "export_blocker",
                "priority": 25, "receipt_id": receipt_id, "subject_id": receipt_id,
                "title": "Exportot blokkoló adat",
                "reason": first["message"], "action_label": "Javítás",
                "action_url": f"#receipts?receipt={receipt_id}&field={field}", "created_at": row["created_at"],
                "issue_code": first["code"], "field": field,
            })
        if actor.role in {"admin", "reviewer"}:
            approvals = self._db.execute(
                "SELECT approval_id,receipt_id,created_at FROM approvals "
                "WHERE tenant_id=? AND status='pending'", (actor.tenant_id,),
            ).fetchall()
            for row in approvals:
                items.append({
                    "task_id": "approval:" + row["approval_id"], "type": "approval",
                    "priority": 30, "receipt_id": row["receipt_id"], "subject_id": row["approval_id"],
                    "title": "Jóváhagyásra vár",
                    "reason": "A tétel döntést igényel.", "action_label": "Megnyitás",
                    "action_url": f'#approvals?approval={row["approval_id"]}', "created_at": row["created_at"],
                })
        return {"items": items[:limit], "total": len(items),
                "counts": {kind: sum(i["type"] == kind for i in items)
                           for kind in ("failed_job", "review", "export_blocker", "approval")}}
    # --- F1.3 magic-link lifecycle -------------------------------------------
    def create_magic_link(
        self,
        email: str,
        *,
        tenant_id: str | None = None,
        role: str | None = None,
        ttl_seconds: int = MAGIC_LINK_TTL_SECONDS,
    ) -> dict[str, Any]:
        """Create a single-use, expiring magic-link token for *email*."""
        token = secrets.token_urlsafe(32)
        now = self._now()
        expires = datetime.fromisoformat(now).timestamp() + ttl_seconds
        with self._db:
            self._db.execute(
                "INSERT INTO auth_tokens(token_hash,email,purpose,tenant_id,role,invite_id,"
                "expires_at,consumed_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (_sha256(token), email.strip().lower(), "login", tenant_id, role, None,
                 datetime.fromtimestamp(expires, UTC).isoformat(), None, now),
            )
            self._audit(tenant_id or "unclaimed", "auth.magic_link_created", email.strip().lower())
        return {"token": token, "email": email.strip().lower(), "expires_at": datetime.fromtimestamp(expires, UTC).isoformat()}

    def verify_magic_link(self, token: str) -> dict[str, Any]:
        """Consume a magic-link token and return its payload (KeyError on bad)."""
        digest = _sha256(token)
        now = self._now()
        with self._lock, self._db:
            row = self._db.execute(
                "SELECT * FROM auth_tokens WHERE token_hash=? AND purpose='login'",
                (digest,),
            ).fetchone()
            if not row:
                raise KeyError("unknown magic-link token")
            if row["consumed_at"] is not None:
                raise KeyError("magic-link token already used")
            if row["expires_at"] <= now:
                raise KeyError("magic-link token expired")
            self._db.execute(
                "UPDATE auth_tokens SET consumed_at=? WHERE token_hash=?",
                (now, digest),
            )
            self._audit(row["tenant_id"] or "unclaimed", "auth.magic_link_verified", row["email"])
            return {
                "email": row["email"],
                "tenant_id": row["tenant_id"],
                "role": row["role"],
                "invite_id": row["invite_id"],
            }

    # --- F1.3 sessions -------------------------------------------------------
    def create_session(
        self,
        email: str,
        tenant_id: str,
        role: str,
        *,
        ttl_seconds: int = SESSION_TTL_SECONDS,
        display_name: str | None = None,
    ) -> dict[str, Any]:
        """Create a session token bound to a household role."""
        token = secrets.token_urlsafe(32)
        now = self._now()
        expires = datetime.fromisoformat(now).timestamp() + ttl_seconds
        with self._db:
            self._db.execute(
                "INSERT INTO sessions(session_token,email,tenant_id,role,expires_at,created_at,display_name)"
                " VALUES(?,?,?,?,?,?,?)",
                (token, email.strip().lower(), tenant_id, role,
                 datetime.fromtimestamp(expires, UTC).isoformat(), now, display_name),
            )
            self._audit(tenant_id, "auth.session_created", email.strip().lower())
        return {"session_token": token, "email": email.strip().lower(), "tenant_id": tenant_id,
                "role": role, "expires_at": datetime.fromtimestamp(expires, UTC).isoformat(),
                "display_name": display_name}

    def resolve_session(self, session_token: str) -> dict[str, Any]:
        """Resolve a session token into an identity or raise ``KeyError``.

        On success the expiry is extended (sliding session) — every
        authenticated request refreshes the TTL so the login persists as long
        as the user keeps using the app (goal: stays logged in until explicit
        sign-out).  The update is best-effort: a write failure does not fail
        the read.
        """
        row = self._db.execute(
            "SELECT * FROM sessions WHERE session_token=?",
            (session_token,),
        ).fetchone()
        if not row:
            raise KeyError("unknown session")
        if row["expires_at"] <= self._now():
            raise KeyError("session expired")
        try:
            new_exp = datetime.fromisoformat(self._now()).timestamp() + SESSION_TTL_SECONDS
            self._db.execute(
                "UPDATE sessions SET expires_at=? WHERE session_token=?",
                (datetime.fromtimestamp(new_exp, UTC).isoformat(), session_token),
            )
            self._db.commit()
        except Exception:
            pass
        dn = None
        try:
            dn = row["display_name"] if "display_name" in row.keys() else None
        except Exception:
            pass
        return {"email": row["email"], "tenant_id": row["tenant_id"], "role": row["role"], "display_name": dn}

    def delete_session(self, session_token: str) -> bool:
        """Delete a session token. Returns True when a row was removed."""
        with self._db:
            cur = self._db.execute("DELETE FROM sessions WHERE session_token=?", (session_token,))
            if cur.rowcount:
                self._db.commit()
            return cur.rowcount > 0

    def find_or_create_household_owner(self, email: str) -> tuple[str, bool]:
        """Find or create a household for *email* with an ``owner`` member row.

        Returns ``(tenant_id, created)`` where *created* is ``True`` when a new
        household and member row were inserted.  The household id is derived
        deterministically from the email (``hh-{email}``).
        """
        email_norm = email.strip().lower()
        tenant_id = f"hh-{email_norm.replace('@', '-').replace('.', '-')}"
        with self._db:
            existing = self._db.execute(
                "SELECT 1 FROM members WHERE tenant_id=? AND email=? AND role='owner'",
                (tenant_id, email_norm),
            ).fetchone()
            if existing:
                return tenant_id, False
            member_id = str(uuid.uuid4())
            self._db.execute(
                "INSERT INTO members(member_id,tenant_id,email,role,active) VALUES(?,?,?,?,1)",
                (member_id, tenant_id, email_norm, "owner"),
            )
            self._audit(tenant_id, "member.created", member_id)
        return tenant_id, True

    # --- F1.3 household invites ----------------------------------------------
    def create_invite(
        self,
        actor: Actor,
        email: str,
        role: str,
        *,
        ttl_seconds: int = INVITE_TTL_SECONDS,
    ) -> dict[str, Any]:
        """Create a family invite (owner only).  Returns the raw invite token once."""
        if not self.can_manage_household(actor):
            raise PermissionError("only the household owner can invite members")
        if role not in HOUSEHOLD_ROLES:
            raise ValueError("invalid household role")
        if role == "owner":
            raise ValueError("a household has exactly one owner")
        token = secrets.token_urlsafe(32)
        now = self._now()
        expires = datetime.fromisoformat(now).timestamp() + ttl_seconds
        invite_id = str(uuid.uuid4())
        with self._db:
            self._db.execute(
                "INSERT INTO household_invites(invite_id,tenant_id,email,role,invited_by,status,"
                "token_hash,created_at,accepted_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (invite_id, actor.tenant_id, email.strip().lower(), role, actor.tenant_id,
                 "pending", _sha256(token), now, None),
            )
            self._db.execute(
                "INSERT INTO auth_tokens(token_hash,email,purpose,tenant_id,role,invite_id,"
                "expires_at,consumed_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (_sha256(token), email.strip().lower(), "invite", actor.tenant_id, role, invite_id,
                 datetime.fromtimestamp(expires, UTC).isoformat(), None, now),
            )
            self._audit(actor.tenant_id, "invite.created", invite_id)
        return {"invite_id": invite_id, "email": email.strip().lower(), "role": role,
                "status": "pending", "expires_at": datetime.fromtimestamp(expires, UTC).isoformat(),
                "token": token}

    def list_invites(self, actor: Actor) -> list[dict[str, Any]]:
        """List the household's pending invites (owner only)."""
        if not self.can_manage_household(actor):
            raise PermissionError("only the household owner can list invites")
        rows = self._db.execute(
            "SELECT invite_id,email,role,status,created_at,accepted_at FROM household_invites "
            "WHERE tenant_id=? ORDER BY created_at DESC",
            (actor.tenant_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def accept_invite(
        self,
        token: str,
        *,
        expected_tenant_id: str | None = None,
        expected_invite_id: str | None = None,
    ) -> dict[str, Any]:
        """Accept a family invite: creates a membership + a session in one step.

        ``expected_tenant_id``/``expected_invite_id`` are the ids carried in
        the accept URL.  When supplied, they are validated BEFORE the token
        is consumed, so a wrong-household path (404) never burns a valid
        invite token (F1.3 review MED-6).
        """
        digest = _sha256(token)
        now = self._now()
        with self._lock, self._db:
            row = self._db.execute(
                "SELECT * FROM auth_tokens WHERE token_hash=? AND purpose='invite'",
                (digest,),
            ).fetchone()
            if not row:
                raise KeyError("unknown invite token")
            if row["consumed_at"] is not None:
                raise KeyError("invite token already used")
            if row["expires_at"] <= now:
                raise KeyError("invite token expired")
            tenant_id, role, email, invite_id = row["tenant_id"], row["role"], row["email"], row["invite_id"]
            if expected_tenant_id is not None and tenant_id != expected_tenant_id:
                raise KeyError("invite token does not match the household path")
            if expected_invite_id is not None and invite_id != expected_invite_id:
                raise KeyError("invite token does not match the invite path")
            self._db.execute("UPDATE auth_tokens SET consumed_at=? WHERE token_hash=?", (now, digest))
            self._db.execute(
                "UPDATE household_invites SET status='accepted', accepted_at=? WHERE invite_id=?",
                (now, invite_id),
            )
            existing = self._db.execute(
                "SELECT member_id FROM members WHERE tenant_id=? AND email=?",
                (tenant_id, email),
            ).fetchone()
            if existing:
                self._db.execute(
                    "UPDATE members SET role=?, active=1 WHERE member_id=?",
                    (role, existing["member_id"]),
                )
                member_id = existing["member_id"]
            else:
                member_id = str(uuid.uuid4())
                self._db.execute(
                    "INSERT INTO members(member_id,tenant_id,email,role,active) VALUES(?,?,?,?,1)",
                    (member_id, tenant_id, email, role),
                )
            self._audit(tenant_id, "invite.accepted", invite_id)
        session = self.create_session(email, tenant_id, role)
        return {**session, "invite_id": invite_id, "member_id": member_id}

    # --- F1.3 role helpers ---------------------------------------------------
    @staticmethod
    def household_role_of(actor: Actor) -> str:
        """Map a wire role (legacy header or household) to a household role.

        Legacy dev-header roles map to RESTRICTED household roles — the
        demo headers must never grant owner-equivalent power (F1.3 review
        CRITICAL-2): ``admin``/``reviewer`` -> ``adult`` (can write), and
        ``integrator`` -> ``child`` (read-mostly).  Household roles pass
        through unchanged.
        """
        role = actor.role
        if role in HOUSEHOLD_ROLES:
            return role
        if role in {"admin", "reviewer"}:
            return "adult"
        return "child"

    @staticmethod
    def can_write(actor: Actor) -> bool:
        """True when the actor may mutate household data (edit/upload)."""
        return ProductService.household_role_of(actor) in WRITE_ROLES

    @staticmethod
    def can_manage_household(actor: Actor) -> bool:
        """True when the actor may invite members / manage household settings."""
        return ProductService.household_role_of(actor) == "owner"

    def dashboard(self, actor: Actor) -> dict[str, Any]:
        jobs=self.list_jobs(actor); total=len(jobs)
        statuses={}
        for job in jobs: statuses[job["status"]]=statuses.get(job["status"],0)+1
        reviewed=self._db.execute("SELECT COUNT(*) FROM audit WHERE tenant_id=? AND action='receipt.corrected'",(actor.tenant_id,)).fetchone()[0]
        return {
            "usage":{"documents":total,"jobs_by_status":statuses},
            "quality":{"needs_review":statuses.get("needs_review",0),"corrections":reviewed},
            "privacy":{"retention_days":self.retention_days(actor),"region":"local","content_logging":False},
            "service":{"status":"ready","p95_ms":None},
        }
