"""Idempotent 50-item accounting sync."""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class SyncResult:
    pushed: int
    failed: int
    errors: list[dict[str, str]]
    provider: str


class SyncService:
    def __init__(self, service):
        self.db = service._db
        with self.db:
            self.db.executescript(
                "CREATE TABLE IF NOT EXISTS receipt_sync(tenant_id TEXT,receipt_id TEXT,provider TEXT,remote_id TEXT,PRIMARY KEY(tenant_id,receipt_id,provider));CREATE TABLE IF NOT EXISTS integration_connections(tenant_id TEXT,provider TEXT,org_name TEXT,external_id TEXT,status TEXT,connected_at TEXT,PRIMARY KEY(tenant_id,provider));"
            )

    def push(self, tenant, provider, date_from, date_to, push_batch):
        if provider not in {"qbo", "xero"}:
            raise ValueError("provider must be qbo or xero")
        items = []
        for row in self.db.execute(
            "SELECT receipt_id,payload FROM receipts WHERE tenant_id=?", (tenant,)
        ).fetchall():
            p = json.loads(row["payload"])
            d = str(p.get("date") or "")
            if (
                date_from <= d <= date_to
                and not self.db.execute(
                    "SELECT 1 FROM receipt_sync WHERE tenant_id=? AND receipt_id=? AND provider=?",
                    (tenant, row["receipt_id"], provider),
                ).fetchone()
            ):
                items.append({"receipt_id": row["receipt_id"], **p})
        pushed = failed = 0
        errors = []
        for start in range(0, len(items), 50):
            batch = items[start : start + 50]
            try:
                result = push_batch(batch)
                with self.db:
                    for i, x in enumerate(batch):
                        self.db.execute(
                            "INSERT OR IGNORE INTO receipt_sync VALUES(?,?,?,?)",
                            (
                                tenant,
                                x["receipt_id"],
                                provider,
                                str(
                                    (result[i] if i < len(result) else {}).get("Id")
                                    or x["receipt_id"]
                                ),
                            ),
                        )
                        pushed += 1
            except Exception as e:
                failed += len(batch)
                errors += [{"receipt_id": x["receipt_id"], "error": str(e)[:200]} for x in batch]
        return SyncResult(pushed, failed, errors, provider)

    def list_connections(self, t):
        return [
            dict(x)
            for x in self.db.execute(
                "SELECT * FROM integration_connections WHERE tenant_id=?", (t,)
            ).fetchall()
        ]
