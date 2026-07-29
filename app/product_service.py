"""Application services for the user-facing ReceiptLens product workflows.

The service owns workflow state and tenant isolation. Storage is expressed as a
small SQLite database so jobs, reviews, memberships, connections, and audit
metadata survive process restarts without coupling HTTP handlers to SQL.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ProductConflict(RuntimeError):
    """Raised for stale versions or invalid job state changes."""


@dataclass(frozen=True)
class Actor:
    tenant_id: str
    role: str


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
            """)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _audit(self, tenant: str, action: str, subject: str | None = None) -> None:
        self._db.execute("INSERT INTO audit VALUES(?,?,?,?,?)", (str(uuid.uuid4()), tenant, action, subject, self._now()))

    @staticmethod
    def _receipt_payload(receipt: Any) -> dict[str, Any]:
        return {
            "vendor": receipt.merchant, "date": receipt.date, "total": receipt.total,
            "tax": receipt.tax, "currency": receipt.currency,
            "line_items": [{"name": i.name, "price": i.price} for i in receipt.items],
            "confidence": dict(receipt.confidence),
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

    def list_reviews(self, actor: Actor) -> list[dict[str, Any]]:
        rows = self._db.execute("SELECT * FROM receipts WHERE tenant_id=? AND status='needs_review' ORDER BY created_at", (actor.tenant_id,)).fetchall()
        return [{"receipt_id": r["receipt_id"], "status": r["status"], "version": r["version"], "receipt": json.loads(r["payload"])} for r in rows]

    def correct(self, actor: Actor, receipt_id: str, changes: dict[str, Any], expected_version: int, complete: bool) -> dict[str, Any]:
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
        if actor.role != "admin": raise PermissionError
        if role not in {"admin", "reviewer", "integrator"}: raise ValueError("invalid role")
        member_id = str(uuid.uuid4())
        with self._db:
            self._db.execute("INSERT INTO members VALUES(?,?,?,?,1)", (member_id, actor.tenant_id, email.lower(), role))
            self._audit(actor.tenant_id, "member.created", member_id)
        return {"member_id": member_id, "email": email.lower(), "role": role, "active": True}

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

    def dashboard(self, actor: Actor) -> dict[str, Any]:
        jobs=self.list_jobs(actor); total=len(jobs)
        statuses={}
        for job in jobs: statuses[job["status"]]=statuses.get(job["status"],0)+1
        reviewed=self._db.execute("SELECT COUNT(*) FROM audit WHERE tenant_id=? AND action='receipt.corrected'",(actor.tenant_id,)).fetchone()[0]
        return {
            "usage":{"documents":total,"jobs_by_status":statuses},
            "quality":{"needs_review":statuses.get("needs_review",0),"corrections":reviewed},
            "privacy":{"retention_days":30,"region":"local","content_logging":False},
            "service":{"status":"ready","p95_ms":None},
        }
