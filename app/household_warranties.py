"""Warranty and return deadlines a household wants to be reminded about.

Stored in the product database, scoped to the household (tenant). Dates are
worked out here, not in the browser, so every surface agrees on the same
deadline and on what "days left" means.
"""
from __future__ import annotations

import calendar
import sqlite3
import threading
import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

#: A deadline this close is shown as due soon.
DUE_SOON_DAYS = 14
STATUSES = {"active", "returned", "claim", "archived"}


def _today() -> date:
    """Current UTC date — one indirection so tests can pin the day."""
    return datetime.now(UTC).date()


def add_months(start: date, months: int) -> date:
    """``start`` plus whole months, clamped to the end of a shorter month."""
    index = start.month - 1 + months
    year, month = start.year + index // 12, index % 12 + 1
    return date(year, month, min(start.day, calendar.monthrange(year, month)[1]))


class HouseholdWarranties:
    """Tenant-scoped warranty and return-window records."""

    def __init__(self, service: Any) -> None:
        self.db: sqlite3.Connection = service._db
        self.lock = threading.RLock()
        with self.db:
            self.db.execute("""
            CREATE TABLE IF NOT EXISTS household_warranties(
              warranty_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, receipt_id TEXT,
              item_name TEXT NOT NULL, merchant TEXT, purchase_date TEXT NOT NULL,
              return_days INTEGER NOT NULL, warranty_months INTEGER NOT NULL,
              status TEXT NOT NULL, notes TEXT, created_at TEXT NOT NULL)""")

    @staticmethod
    def _view(row: sqlite3.Row, today: date) -> dict[str, Any]:
        """A record with its deadlines worked out against ``today``."""
        purchased = date.fromisoformat(row["purchase_date"])
        return_by = purchased + timedelta(days=row["return_days"]) if row["return_days"] else None
        warranty_ends = add_months(purchased, row["warranty_months"]) if row["warranty_months"] else None
        # Only a deadline that is still ahead can be the next one.
        ahead = [(d, kind) for d, kind in ((return_by, "return"), (warranty_ends, "warranty"))
                 if d is not None and d >= today]
        next_date, next_kind = min(ahead, default=(None, None))
        days = (next_date - today).days if next_date else None
        return {
            "warranty_id": row["warranty_id"], "receipt_id": row["receipt_id"],
            "item_name": row["item_name"], "merchant": row["merchant"],
            "purchase_date": row["purchase_date"], "return_days": row["return_days"],
            "warranty_months": row["warranty_months"], "status": row["status"], "notes": row["notes"],
            "return_by": return_by.isoformat() if return_by else None,
            "warranty_ends": warranty_ends.isoformat() if warranty_ends else None,
            "return_days_left": (return_by - today).days if return_by else None,
            "warranty_days_left": (warranty_ends - today).days if warranty_ends else None,
            "next_deadline": next_date.isoformat() if next_date else None,
            "next_deadline_kind": next_kind,
            "days_to_next": days,
            "due_soon": row["status"] == "active" and days is not None and days <= DUE_SOON_DAYS,
        }

    def list(self, tenant_id: str, today: date | None = None) -> dict[str, Any]:
        today = today or _today()
        rows = self.db.execute("SELECT * FROM household_warranties WHERE tenant_id=?", (tenant_id,)).fetchall()
        items = [self._view(r, today) for r in rows]
        # Open items first with the nearest deadline on top; closed ones after, newest purchase first.
        active = sorted((i for i in items if i["status"] == "active"),
                        key=lambda i: (i["next_deadline"] is None, i["next_deadline"] or ""))
        closed = sorted((i for i in items if i["status"] != "active"),
                        key=lambda i: i["purchase_date"], reverse=True)
        items = active + closed
        return {"items": items, "summary": {
            "active": sum(1 for i in items if i["status"] == "active"),
            "due_soon": sum(1 for i in items if i["due_soon"]),
        }}

    @staticmethod
    def _clean(body: dict[str, Any], *, partial: bool, today: date) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if "item_name" in body or not partial:
            name = str(body.get("item_name") or "").strip()
            if not 1 <= len(name) <= 200:
                raise ValueError("item_name must be 1 to 200 characters")
            out["item_name"] = name
        if "merchant" in body:
            merchant = str(body["merchant"] or "").strip()[:200]
            out["merchant"] = merchant or None
        if "notes" in body:
            notes = str(body["notes"] or "").strip()[:1000]
            out["notes"] = notes or None
        if "purchase_date" in body or not partial:
            try:
                purchased = date.fromisoformat(str(body.get("purchase_date")))
            except ValueError as exc:
                raise ValueError("purchase_date must be an ISO date (YYYY-MM-DD)") from exc
            if purchased > today + timedelta(days=1):
                raise ValueError("purchase_date cannot be in the future")
            out["purchase_date"] = purchased.isoformat()
        for field, ceiling in (("return_days", 365), ("warranty_months", 120)):
            if field in body or not partial:
                value = body.get(field, 0)
                if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= ceiling:
                    raise ValueError(f"{field} must be a whole number from 0 to {ceiling}")
                out[field] = value
        if "status" in body:
            if body["status"] not in STATUSES:
                raise ValueError("status must be one of: " + ", ".join(sorted(STATUSES)))
            out["status"] = body["status"]
        return out

    def create(self, tenant_id: str, body: dict[str, Any], today: date | None = None) -> dict[str, Any]:
        today = today or _today()
        clean = self._clean(body, partial=False, today=today)
        if not clean["return_days"] and not clean["warranty_months"]:
            raise ValueError("Add a return window or a warranty length")
        warranty_id = str(uuid.uuid4())
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO household_warranties VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (warranty_id, tenant_id, body.get("receipt_id") or None, clean["item_name"],
                 clean.get("merchant"), clean["purchase_date"], clean["return_days"],
                 clean["warranty_months"], "active", clean.get("notes"),
                 datetime.now(UTC).isoformat()))
        return self.get(tenant_id, warranty_id, today)

    def get(self, tenant_id: str, warranty_id: str, today: date | None = None) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM household_warranties WHERE tenant_id=? AND warranty_id=?",
                              (tenant_id, warranty_id)).fetchone()
        if row is None:
            raise KeyError(warranty_id)
        return self._view(row, today or _today())

    def update(self, tenant_id: str, warranty_id: str, body: dict[str, Any],
               today: date | None = None) -> dict[str, Any]:
        today = today or _today()
        self.get(tenant_id, warranty_id, today)
        clean = self._clean(body, partial=True, today=today)
        if clean:
            assignments = ", ".join(f"{column}=?" for column in clean)
            with self.lock, self.db:
                self.db.execute(
                    f"UPDATE household_warranties SET {assignments} WHERE tenant_id=? AND warranty_id=?",  # columns come from _clean's fixed set
                    (*clean.values(), tenant_id, warranty_id))
        return self.get(tenant_id, warranty_id, today)

    def delete(self, tenant_id: str, warranty_id: str) -> None:
        with self.lock, self.db:
            cursor = self.db.execute("DELETE FROM household_warranties WHERE tenant_id=? AND warranty_id=?",
                                     (tenant_id, warranty_id))
        if cursor.rowcount == 0:
            raise KeyError(warranty_id)
