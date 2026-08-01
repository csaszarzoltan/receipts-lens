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

    def search_receipts(self, actor: Actor, query: str | None = None,
                        status: str | None = None, tag: str | None = None,
                        min_total: float | None = None, max_total: float | None = None,
                        limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Search tenant receipts with stable pagination and optional metadata filters."""
        if not 1 <= limit <= 200 or offset < 0:
            raise ValueError("limit must be 1..200 and offset must be non-negative")
        rows = self._db.execute(
            "SELECT r.*,m.tags,m.project,m.cost_center FROM receipts r "
            "LEFT JOIN receipt_metadata m ON m.receipt_id=r.receipt_id "
            "WHERE r.tenant_id=? ORDER BY r.created_at DESC, r.receipt_id", (actor.tenant_id,)
        ).fetchall()
        items=[]
        for row in rows:
            payload=json.loads(row["payload"])
            tags=json.loads(row["tags"] or "[]")
            total=payload.get("total")
            haystack=" ".join(str(payload.get(k) or "") for k in ("vendor","date","currency")).lower()
            if query and query.lower() not in haystack: continue
            if status and row["status"] != status: continue
            if tag and tag.lower() not in {str(x).lower() for x in tags}: continue
            if min_total is not None and (total is None or float(total) < min_total): continue
            if max_total is not None and (total is None or float(total) > max_total): continue
            items.append({"receipt_id":row["receipt_id"],"status":row["status"],
                          "version":row["version"],"created_at":row["created_at"],
                          "receipt":payload,"metadata":{"tags":tags,"project":row["project"],
                          "cost_center":row["cost_center"]}})
        return {"items":items[offset:offset+limit],"total":len(items),"limit":limit,"offset":offset}

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
        current=now or datetime.now(timezone.utc)
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
