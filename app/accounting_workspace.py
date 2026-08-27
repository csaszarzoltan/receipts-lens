"""Accounting-readiness, governance, and operational UI services for ReceiptLens 1.1."""
from __future__ import annotations

import io
import json
import sqlite3
import uuid
import zipfile
from datetime import UTC, date, datetime
from typing import Any


class AccountingWorkspace:
    """Tenant-scoped services backing the 1.1 accounting workspace."""

    def __init__(self, product_service: Any) -> None:
        self.service = product_service
        self.db: sqlite3.Connection = product_service._db
        self._schema()

    @staticmethod
    def now() -> str:
        return datetime.now(UTC).isoformat()

    def _schema(self) -> None:
        with self.db:
            self.db.executescript("""
            CREATE TABLE IF NOT EXISTS exchange_rates(
              rate_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, base TEXT NOT NULL,
              quote TEXT NOT NULL, rate REAL NOT NULL, rate_date TEXT NOT NULL,
              source TEXT NOT NULL, created_at TEXT NOT NULL,
              UNIQUE(tenant_id,base,quote,rate_date));
            CREATE TABLE IF NOT EXISTS approval_flows(
              flow_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL,
              definition TEXT NOT NULL, version INTEGER NOT NULL, active INTEGER NOT NULL,
              created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS inbound_emails(
              email_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, sender TEXT NOT NULL,
              subject TEXT NOT NULL, attachments TEXT NOT NULL, status TEXT NOT NULL,
              error TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS permission_profiles(
              tenant_id TEXT NOT NULL, role TEXT NOT NULL, permissions TEXT NOT NULL,
              updated_at TEXT NOT NULL, PRIMARY KEY(tenant_id,role));
            CREATE TABLE IF NOT EXISTS recurring_feedback(
              tenant_id TEXT NOT NULL, merchant TEXT NOT NULL, is_subscription INTEGER NOT NULL,
              updated_at TEXT NOT NULL, PRIMARY KEY(tenant_id,merchant));
            CREATE TABLE IF NOT EXISTS export_preparations(
              preparation_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, connection_id TEXT,
              receipt_ids TEXT NOT NULL, valid_ids TEXT NOT NULL, blocked TEXT NOT NULL,
              warnings TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
            """)

    def receipt(self, tenant: str, receipt_id: str) -> dict[str, Any]:
        row = self.db.execute("SELECT payload,version,status FROM receipts WHERE tenant_id=? AND receipt_id=?",
                              (tenant, receipt_id)).fetchone()
        if not row:
            raise KeyError(receipt_id)
        return {"payload": json.loads(row["payload"]), "version": row["version"],
                "status": row["status"]}

    def update_line_items(self, actor: Any, receipt_id: str, items: list[dict[str, Any]],
                          expected_version: int) -> dict[str, Any]:
        record = self.receipt(actor.tenant_id, receipt_id)
        if record["version"] != expected_version:
            raise RuntimeError("stale receipt version")
        clean = []
        for index, item in enumerate(items):
            name = str(item.get("name") or "").strip()
            quantity = float(item.get("quantity", 1))
            unit_price = float(item.get("unit_price", item.get("price", 0)))
            amount = float(item.get("amount", quantity * unit_price))
            if not name or quantity <= 0 or unit_price < 0 or amount < 0:
                raise ValueError(f"invalid line item at index {index}")
            clean.append({"name": name, "quantity": quantity, "unit_price": unit_price,
                          "amount": round(amount, 2), "tax_rate": item.get("tax_rate"),
                          "category": item.get("category"), "project": item.get("project"),
                          "cost_center": item.get("cost_center")})
        payload = record["payload"]
        before = list(payload.get("line_items") or [])
        payload["line_items"] = clean
        version = expected_version + 1
        with self.db:
            self.db.execute("UPDATE receipts SET payload=?,version=? WHERE tenant_id=? AND receipt_id=?",
                            (json.dumps(payload, sort_keys=True), version, actor.tenant_id, receipt_id))
        return {"receipt_id": receipt_id, "version": version, "line_items": clean,
                "before": before, "line_items_total": round(sum(x["amount"] for x in clean), 2)}

    def _validate_core_fields(self, payload: dict[str, Any]) -> list[dict[str, str]]:
        """Check required fields and total/tax invariants; return error dicts."""
        errors: list[dict[str, str]] = []
        required = ("vendor", "date", "total", "currency")
        for field in required:
            if payload.get(field) in (None, ""):
                errors.append({"code": f"missing_{field}", "field": field,
                               "message": f"The \"{field}\" field is required."})
        total = payload.get("total")
        tax = payload.get("tax")
        if total is not None and float(total) < 0:
            errors.append({"code": "negative_total", "field": "total",
                           "message": "Total cannot be negative."})
        if tax is not None and total is not None and float(tax) > float(total):
            errors.append({"code": "tax_exceeds_total", "field": "tax",
                           "message": "Tax cannot exceed the total."})
        return errors

    def _validate_date(self, payload: dict[str, Any], errors: list[dict[str, str]],
                       warnings: list[dict[str, str]]) -> None:
        """Check the receipt date format and future dates."""
        try:
            if payload.get("date") and date.fromisoformat(payload["date"]) > datetime.now(UTC).date():
                warnings.append({"code": "future_date", "field": "date",
                                 "message": "Date is in the future."})
        except ValueError:
            errors.append({"code": "invalid_date", "field": "date",
                           "message": "Invalid date format."})

    def _validate_line_items(self, payload: dict[str, Any], total: Any,
                             warnings: list[dict[str, str]]) -> float:
        """Check line-item totals against the receipt total; return item_total."""
        items = payload.get("line_items") or []
        item_total = round(sum(float(i.get("amount", i.get("price", 0)) or 0) for i in items), 2)
        if total is not None and items and abs(item_total - float(total)) > 0.01:
            warnings.append({"code": "line_total_mismatch", "field": "line_items",
                             "message": f"Line items total {item_total:.2f}, receipt total {float(total):.2f}."})
        return item_total

    def _validate_export_context(self, actor: Any, receipt_id: str, connection_id: str | None,
                                 warnings: list[dict[str, str]],
                                 errors: list[dict[str, str]]) -> None:
        """Check cost-center metadata and connection mapping existence."""
        metadata = self.db.execute("SELECT project,cost_center FROM receipt_metadata WHERE tenant_id=? AND receipt_id=?",
                                   (actor.tenant_id, receipt_id)).fetchone()
        if not metadata or not metadata["cost_center"]:
            warnings.append({"code": "missing_cost_center", "field": "cost_center",
                             "message": "No cost center set."})
        if connection_id:
            conn = self.db.execute("SELECT mapping FROM connections WHERE tenant_id=? AND connection_id=?",
                                   (actor.tenant_id, connection_id)).fetchone()
            if not conn:
                errors.append({"code": "connection_missing", "field": "connection",
                               "message": "Export connection not found."})

    def validate(self, actor: Any, receipt_id: str, connection_id: str | None = None) -> dict[str, Any]:
        payload = self.receipt(actor.tenant_id, receipt_id)["payload"]
        errors = self._validate_core_fields(payload)
        warnings: list[dict[str, str]] = []
        self._validate_date(payload, errors, warnings)
        item_total = self._validate_line_items(payload, payload.get("total"), warnings)
        self._validate_export_context(actor, receipt_id, connection_id, warnings, errors)
        readiness = "blocked" if errors else ("warning" if warnings else "exportable")
        return {"receipt_id": receipt_id, "readiness": readiness, "errors": errors,
                "warnings": warnings, "line_items_total": item_total}

    def create_approval_flow(self, actor: Any, name: str, definition: dict[str, Any]) -> dict[str, Any]:
        if actor.role != "admin":
            raise PermissionError
        steps = definition.get("steps") or []
        if not steps:
            raise ValueError("at least one approval step is required")
        for step in steps:
            if step.get("mode") not in {"serial", "parallel"} or not step.get("roles"):
                raise ValueError("invalid approval step")
        flow_id = str(uuid.uuid4())
        with self.db:
            self.db.execute("INSERT INTO approval_flows VALUES(?,?,?,?,1,1,?)",
                            (flow_id, actor.tenant_id, name, json.dumps(definition), self.now()))
        return {"flow_id": flow_id, "name": name, "definition": definition,
                "version": 1, "active": True}

    def approval_flows(self, tenant: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM approval_flows WHERE tenant_id=? ORDER BY name",
                               (tenant,)).fetchall()
        return [{**dict(row), "definition": json.loads(row["definition"]),
                 "active": bool(row["active"])} for row in rows]

    def simulate_approval(self, tenant: str, definition: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
        total = float(receipt.get("total") or 0)
        minimum = float(definition.get("min_total", 0))
        applies = total >= minimum
        return {"applies": applies, "steps": definition.get("steps", []) if applies else [],
                "estimated_approvers": sum(len(s.get("roles", [])) for s in definition.get("steps", [])) if applies else 0}

    def prepare_export(self, actor: Any, receipt_ids: list[str], connection_id: str | None) -> dict[str, Any]:
        valid, blocked, warnings = [], [], []
        for rid in receipt_ids:
            try:
                result = self.validate(actor, rid, connection_id)
            except KeyError:
                blocked.append({"receipt_id": rid, "reason": "not_found"})
                continue
            if result["errors"]:
                blocked.append({"receipt_id": rid, "reason": result["errors"]})
            else:
                valid.append(rid)
                if result["warnings"]:
                    warnings.append({"receipt_id": rid, "warnings": result["warnings"]})
        pid = str(uuid.uuid4())
        status = "ready" if valid and not blocked else ("partial" if valid else "blocked")
        with self.db:
            self.db.execute("INSERT INTO export_preparations(preparation_id,tenant_id,connection_id,receipt_ids,valid_ids,blocked,warnings,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                            (pid, actor.tenant_id, connection_id, json.dumps(receipt_ids),
                             json.dumps(valid), json.dumps(blocked), json.dumps(warnings), status, self.now()))
        return {"preparation_id": pid, "status": status, "requested": len(receipt_ids),
                "valid_ids": valid, "blocked": blocked, "warnings": warnings}

    def export_preparations(self, tenant: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM export_preparations WHERE tenant_id=? ORDER BY created_at DESC",
                               (tenant,)).fetchall()
        return [{**dict(r), "receipt_ids": json.loads(r["receipt_ids"]),
                 "valid_ids": json.loads(r["valid_ids"]), "blocked": json.loads(r["blocked"]),
                 "warnings": json.loads(r["warnings"])} for r in rows]

    def receive_email(self, tenant: str, sender: str, subject: str,
                      attachments: list[dict[str, Any]]) -> dict[str, Any]:
        safe = [{"filename": str(a.get("filename") or "attachment"),
                 "content_type": str(a.get("content_type") or "application/octet-stream"),
                 "size": int(a.get("size", 0))} for a in attachments]
        status = "queued" if any(a["content_type"].startswith(("image/", "application/pdf")) for a in safe) else "quarantined"
        eid = str(uuid.uuid4())
        with self.db:
            self.db.execute("INSERT INTO inbound_emails VALUES(?,?,?,?,?,?,NULL,?)",
                            (eid, tenant, sender, subject, json.dumps(safe), status, self.now()))
        return {"email_id": eid, "sender": sender, "subject": subject,
                "attachments": safe, "status": status}

    def emails(self, tenant: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM inbound_emails WHERE tenant_id=? ORDER BY created_at DESC",
                               (tenant,)).fetchall()
        return [{**dict(r), "attachments": json.loads(r["attachments"])} for r in rows]

    def recurring(self, tenant: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT payload FROM receipts WHERE tenant_id=?", (tenant,)).fetchall()
        groups: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            payload = json.loads(row["payload"])
            merchant = str(payload.get("vendor") or "Unknown")
            groups.setdefault(merchant, []).append(payload)
        result = []
        for merchant, receipts in groups.items():
            if len(receipts) < 2:
                continue
            # Order charges chronologically (payload dates are ISO strings) so
            # ``price_change`` and the price-increase check compare like-for-like.
            receipts.sort(key=lambda r: str(r.get("date") or ""))
            amounts = [float(r.get("total") or 0) for r in receipts]
            average = sum(amounts) / len(amounts)
            variance = max(amounts) - min(amounts)
            feedback = self.db.execute("SELECT is_subscription FROM recurring_feedback WHERE tenant_id=? AND merchant=?",
                                       (tenant, merchant)).fetchone()
            likely = variance <= max(1.0, average * .1)
            if feedback:
                likely = bool(feedback[0])
            # Most recent charge date drives the renewal computation.  Guard
            # against legacy payloads that may carry ``None`` or odd formats.
            last_date = ""
            for r in reversed(receipts):
                raw = r.get("date")
                if raw:
                    try:
                        date.fromisoformat(str(raw))
                        last_date = str(raw)
                        break
                    except ValueError:
                        continue
            result.append({"merchant": merchant, "occurrences": len(receipts),
                           "average_amount": round(average, 2), "annualized": round(average * 12, 2),
                           "likely_subscription": likely, "price_change": round(amounts[-1] - amounts[0], 2),
                           "last_date": last_date, "amounts": [round(a, 2) for a in amounts]})
        return sorted(result, key=lambda x: x["annualized"], reverse=True)

    def recurring_feedback(self, tenant: str, merchant: str, is_subscription: bool) -> dict[str, Any]:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO recurring_feedback VALUES(?,?,?,?)",
                            (tenant, merchant, int(is_subscription), self.now()))
        return {"merchant": merchant, "is_subscription": is_subscription}

    def set_rate(self, actor: Any, base: str, quote: str, rate: float,
                 rate_date: str, source: str = "manual") -> dict[str, Any]:
        if actor.role != "admin" or rate <= 0:
            raise PermissionError if actor.role != "admin" else ValueError("rate must be positive")
        rate_id = str(uuid.uuid4())
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO exchange_rates VALUES(?,?,?,?,?,?,?,?)",
                            (rate_id, actor.tenant_id, base.upper(), quote.upper(), rate,
                             rate_date, source, self.now()))
        return {"base": base.upper(), "quote": quote.upper(), "rate": rate,
                "rate_date": rate_date, "source": source}

    def convert(self, tenant: str, amount: float, base: str, quote: str,
                rate_date: str | None = None) -> dict[str, Any]:
        if base.upper() == quote.upper():
            return {"original": amount, "converted": amount, "rate": 1.0,
                    "base": base.upper(), "quote": quote.upper(), "source": "identity"}
        row = self.db.execute("SELECT rate,rate_date,source FROM exchange_rates WHERE tenant_id=? "
                              "AND base=? AND quote=? AND rate_date<=? ORDER BY rate_date DESC LIMIT 1",
                              (tenant, base.upper(), quote.upper(), rate_date or datetime.now(UTC).date().isoformat())).fetchone()
        if not row:
            raise KeyError("exchange rate not found")
        return {"original": amount, "converted": round(amount * row["rate"], 2),
                "rate": row["rate"], "base": base.upper(), "quote": quote.upper(),
                "rate_date": row["rate_date"], "source": row["source"]}

    def permission_matrix(self, tenant: str) -> dict[str, list[str]]:
        defaults = {
            "admin": ["view_image", "edit_receipt", "approve", "export", "delete", "manage_keys", "manage_rules", "view_audit"],
            "reviewer": ["view_image", "edit_receipt", "approve", "view_audit"],
            "integrator": ["export"],
        }
        rows = self.db.execute("SELECT role,permissions FROM permission_profiles WHERE tenant_id=?", (tenant,)).fetchall()
        for row in rows:
            defaults[row["role"]] = json.loads(row["permissions"])
        return defaults

    def set_permissions(self, actor: Any, role: str, permissions: list[str]) -> dict[str, Any]:
        if actor.role != "admin":
            raise PermissionError
        allowed = {"view_image", "edit_receipt", "approve", "export", "delete", "manage_keys", "manage_rules", "view_audit"}
        if role not in {"admin", "reviewer", "integrator"} or set(permissions) - allowed:
            raise ValueError("invalid permissions")
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO permission_profiles VALUES(?,?,?,?)",
                            (actor.tenant_id, role, json.dumps(sorted(set(permissions))), self.now()))
        return {"role": role, "permissions": sorted(set(permissions))}

    def diagnostic_zip(self, tenant: str, app_version: str) -> bytes:
        health = {"version": app_version, "tenant": tenant, "generated_at": self.now(),
                  "database": "ok", "receipt_count": self.db.execute(
                      "SELECT COUNT(*) FROM receipts WHERE tenant_id=?", (tenant,)).fetchone()[0],
                  "failed_jobs": self.db.execute(
                      "SELECT COUNT(*) FROM jobs WHERE tenant_id=? AND status='failed'", (tenant,)).fetchone()[0]}
        routes = {"features": ["ocr", "review", "approval", "export", "automation", "pwa"]}
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("health.json", json.dumps(health, indent=2, sort_keys=True))
            archive.writestr("capabilities.json", json.dumps(routes, indent=2, sort_keys=True))
            archive.writestr("README.txt", "Diagnostic bundle excludes receipt contents, images, API keys, tokens, and secrets.\n")
        return output.getvalue()
