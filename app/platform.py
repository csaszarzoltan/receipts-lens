"""Durable, tenant-scoped data-plane primitives.

SQLite is the zero-dependency reference adapter.  The public service boundary is
storage-engine neutral so a PostgreSQL adapter can replace it without changing
application code.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class ConflictError(RuntimeError):
    """Raised when optimistic locking detects a stale writer."""


class JobState(str, Enum):
    RECEIVED = "received"
    QUEUED = "queued"
    PROCESSING = "processing"
    NEEDS_REVIEW = "needs_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ALLOWED = {
    JobState.QUEUED: {JobState.PROCESSING, JobState.CANCELLED},
    JobState.PROCESSING: {JobState.COMPLETED, JobState.FAILED, JobState.NEEDS_REVIEW},
    JobState.NEEDS_REVIEW: {JobState.COMPLETED, JobState.FAILED},
    JobState.FAILED: {JobState.QUEUED},
}


@dataclass(frozen=True)
class Submission:
    receipt_id: str
    job_id: str


@dataclass(frozen=True)
class Job:
    job_id: str
    tenant_id: str
    receipt_id: str
    state: JobState
    version: int
    lease_owner: str | None
    lease_until: str | None


class SqliteDataPlane:
    """Transactional reference repository, queue, idempotency and outbox."""

    SCHEMA_VERSION = 1

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._migrate()

    def _migrate(self) -> None:
        with self._db:
            self._db.executescript("""
            CREATE TABLE IF NOT EXISTS schema_version(version INTEGER NOT NULL);
            INSERT INTO schema_version(version)
              SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM schema_version);
            CREATE TABLE IF NOT EXISTS receipts(
              receipt_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, payload TEXT NOT NULL,
              blob_ref TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL, deleted_at TEXT);
            CREATE INDEX IF NOT EXISTS ix_receipts_tenant ON receipts(tenant_id, receipt_id);
            CREATE TABLE IF NOT EXISTS jobs(
              job_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, receipt_id TEXT NOT NULL,
              state TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
              lease_owner TEXT, lease_until TEXT, created_at TEXT NOT NULL,
              FOREIGN KEY(receipt_id) REFERENCES receipts(receipt_id));
            CREATE TABLE IF NOT EXISTS idempotency(
              tenant_id TEXT NOT NULL, idem_key TEXT NOT NULL, response TEXT NOT NULL,
              expires_at TEXT NOT NULL, PRIMARY KEY(tenant_id, idem_key));
            CREATE TABLE IF NOT EXISTS outbox(
              event_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, event_type TEXT NOT NULL,
              payload TEXT NOT NULL, created_at TEXT NOT NULL, delivered_at TEXT);
            """)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def submit_receipt(self, tenant_id: str, payload: dict[str, Any], idempotency_key: str,
                       blob_ref: str) -> Submission:
        if not tenant_id or not idempotency_key or not blob_ref:
            raise ValueError("tenant_id, idempotency_key and blob_ref are required")
        now = self._now(); expires = now + timedelta(hours=24)
        with self._lock, self._db:
            old = self._db.execute(
                "SELECT response, expires_at FROM idempotency WHERE tenant_id=? AND idem_key=?",
                (tenant_id, idempotency_key),
            ).fetchone()
            if old and datetime.fromisoformat(old["expires_at"]) > now:
                return Submission(**json.loads(old["response"]))
            receipt_id, job_id = str(uuid.uuid4()), str(uuid.uuid4())
            self._db.execute("INSERT INTO receipts VALUES(?,?,?,?,1,?,NULL)",
                             (receipt_id, tenant_id, json.dumps(payload, sort_keys=True), blob_ref, now.isoformat()))
            self._db.execute("INSERT INTO jobs VALUES(?,?,?,?,1,NULL,NULL,?)",
                             (job_id, tenant_id, receipt_id, JobState.QUEUED.value, now.isoformat()))
            result = Submission(receipt_id, job_id)
            response = json.dumps(result.__dict__, sort_keys=True)
            self._db.execute("INSERT OR REPLACE INTO idempotency VALUES(?,?,?,?)",
                             (tenant_id, idempotency_key, response, expires.isoformat()))
            self._db.execute("INSERT INTO outbox VALUES(?,?,?,?,?,NULL)",
                             (str(uuid.uuid4()), tenant_id, "receipt.submitted", response, now.isoformat()))
            return result

    def get_receipt(self, tenant_id: str, receipt_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT payload FROM receipts WHERE tenant_id=? AND receipt_id=? AND deleted_at IS NULL",
            (tenant_id, receipt_id),
        ).fetchone()
        return json.loads(row["payload"]) if row else None

    def claim_job(self, worker_id: str, lease_seconds: int = 60) -> Job | None:
        now = self._now(); lease_until = now + timedelta(seconds=lease_seconds)
        with self._lock, self._db:
            row = self._db.execute(
                "SELECT * FROM jobs WHERE state=? OR (state=? AND lease_until<?) ORDER BY created_at LIMIT 1",
                (JobState.QUEUED.value, JobState.PROCESSING.value, now.isoformat()),
            ).fetchone()
            if not row:
                return None
            version = row["version"] + 1
            self._db.execute(
                "UPDATE jobs SET state=?,version=?,lease_owner=?,lease_until=? WHERE job_id=? AND version=?",
                (JobState.PROCESSING.value, version, worker_id, lease_until.isoformat(), row["job_id"], row["version"]),
            )
            return Job(row["job_id"], row["tenant_id"], row["receipt_id"], JobState.PROCESSING,
                       version, worker_id, lease_until.isoformat())

    def transition_job(self, job_id: str, target: JobState, expected_version: int) -> Job:
        with self._lock, self._db:
            row = self._db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
            if not row:
                raise KeyError(job_id)
            current = JobState(row["state"])
            if row["version"] != expected_version:
                raise ConflictError("stale job version")
            if target not in _ALLOWED.get(current, set()):
                raise ValueError(f"invalid transition: {current.value} -> {target.value}")
            version = expected_version + 1
            cursor = self._db.execute(
                "UPDATE jobs SET state=?,version=?,lease_owner=NULL,lease_until=NULL WHERE job_id=? AND version=?",
                (target.value, version, job_id, expected_version),
            )
            if cursor.rowcount != 1:
                raise ConflictError("concurrent job update")
            return Job(job_id, row["tenant_id"], row["receipt_id"], target, version, None, None)

    def close(self) -> None:
        self._db.close()
