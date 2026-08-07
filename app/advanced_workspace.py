"""Advanced workspace capabilities for the consolidated ReceiptLens 1.0 release."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def extract_ocr_boxes(image_bytes: bytes) -> list[dict[str, Any]]:
    """Return normalized Tesseract word boxes; failure keeps upload available."""
    try:
        import pytesseract
        from pytesseract import Output
        from app.preprocessing import preprocess_image
        image = preprocess_image(image_bytes)
        width, height = image.size
        data = pytesseract.image_to_data(image, output_type=Output.DICT,
                                         config="--oem 3 --psm 6")
        boxes = []
        for index, text in enumerate(data.get("text", [])):
            text = str(text).strip()
            confidence = float(data["conf"][index])
            if not text or confidence < 0:
                continue
            boxes.append({
                "text": text, "confidence": round(confidence / 100, 3),
                "x": round(int(data["left"][index]) / width, 5),
                "y": round(int(data["top"][index]) / height, 5),
                "width": round(int(data["width"][index]) / width, 5),
                "height": round(int(data["height"][index]) / height, 5),
            })
        return boxes
    except Exception:
        return []


@dataclass(frozen=True)
class Asset:
    content: bytes
    content_type: str
    filename: str
    boxes: list[dict[str, Any]]


class AdvancedWorkspace:
    """Tenant-safe persistence for UI features that augment ProductService."""

    def __init__(self, service: Any) -> None:
        self.service = service
        self.db: sqlite3.Connection = service._db
        self.lock = threading.RLock()
        self._schema()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _schema(self) -> None:
        with self.db:
            self.db.executescript("""
            CREATE TABLE IF NOT EXISTS receipt_assets(
              receipt_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, content BLOB NOT NULL,
              content_type TEXT NOT NULL, filename TEXT NOT NULL, sha256 TEXT NOT NULL,
              boxes TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS saved_views(
              view_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL,
              filters TEXT NOT NULL, shared INTEGER NOT NULL, pinned INTEGER NOT NULL,
              created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS notifications(
              notification_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, kind TEXT NOT NULL,
              title TEXT NOT NULL, message TEXT NOT NULL, subject_id TEXT,
              read_at TEXT, archived INTEGER NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS automation_rules(
              rule_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL,
              conditions TEXT NOT NULL, actions TEXT NOT NULL, priority INTEGER NOT NULL,
              active INTEGER NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS activity_history(
              history_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, subject_id TEXT NOT NULL,
              action TEXT NOT NULL, before_json TEXT, after_json TEXT,
              actor_role TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS duplicate_decisions(
              decision_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, left_id TEXT NOT NULL,
              right_id TEXT NOT NULL, decision TEXT NOT NULL, created_at TEXT NOT NULL,
              UNIQUE(tenant_id,left_id,right_id));
            CREATE TABLE IF NOT EXISTS user_preferences(
              tenant_id TEXT NOT NULL, role TEXT NOT NULL, payload TEXT NOT NULL,
              updated_at TEXT NOT NULL, PRIMARY KEY(tenant_id,role));
            CREATE TABLE IF NOT EXISTS export_runs(
              run_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, format TEXT NOT NULL,
              status TEXT NOT NULL, requested INTEGER NOT NULL, exported INTEGER NOT NULL,
              errors TEXT NOT NULL, created_at TEXT NOT NULL);
            """)

    def store_asset(self, tenant_id: str, receipt_id: str, content: bytes,
                    content_type: str, filename: str,
                    boxes: list[dict[str, Any]] | None = None) -> None:
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO receipt_assets VALUES(?,?,?,?,?,?,?,?)",
                (receipt_id, tenant_id, content, content_type, filename,
                 hashlib.sha256(content).hexdigest(), json.dumps(boxes or []), self._now()),
            )

    def asset(self, tenant_id: str, receipt_id: str) -> Asset | None:
        row = self.db.execute(
            "SELECT content,content_type,filename,boxes FROM receipt_assets "
            "WHERE tenant_id=? AND receipt_id=?", (tenant_id, receipt_id),
        ).fetchone()
        return Asset(row["content"], row["content_type"], row["filename"],
                     json.loads(row["boxes"])) if row else None

    def delete_assets(self, tenant_id: str, receipt_ids: list[str]) -> None:
        with self.db:
            for receipt_id in receipt_ids:
                self.db.execute("DELETE FROM receipt_assets WHERE tenant_id=? AND receipt_id=?",
                                (tenant_id, receipt_id))

    def notify(self, tenant_id: str, kind: str, title: str, message: str,
               subject_id: str | None = None) -> dict[str, Any]:
        nid, now = str(uuid.uuid4()), self._now()
        with self.db:
            self.db.execute("INSERT INTO notifications VALUES(?,?,?,?,?,?,NULL,0,?)",
                            (nid, tenant_id, kind, title, message, subject_id, now))
        return {"notification_id": nid, "kind": kind, "title": title,
                "message": message, "subject_id": subject_id, "read": False,
                "created_at": now}

    def notifications(self, tenant_id: str, include_archived: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM notifications WHERE tenant_id=?"
        params: list[Any] = [tenant_id]
        if not include_archived:
            query += " AND archived=0"
        query += " ORDER BY created_at DESC"
        rows = self.db.execute(query, params).fetchall()
        return [{**dict(row), "read": row["read_at"] is not None,
                 "archived": bool(row["archived"])} for row in rows]

    def update_notification(self, tenant_id: str, notification_id: str,
                            read: bool | None, archived: bool | None) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM notifications WHERE tenant_id=? AND notification_id=?",
                              (tenant_id, notification_id)).fetchone()
        if not row:
            raise KeyError(notification_id)
        read_at = self._now() if read else (None if read is False else row["read_at"])
        archive_value = int(archived) if archived is not None else row["archived"]
        with self.db:
            self.db.execute("UPDATE notifications SET read_at=?,archived=? WHERE notification_id=?",
                            (read_at, archive_value, notification_id))
        return {"notification_id": notification_id, "read": read_at is not None,
                "archived": bool(archive_value)}

    def mark_all_read(self, tenant_id: str) -> int:
        with self.db:
            cur = self.db.execute("UPDATE notifications SET read_at=? WHERE tenant_id=? "
                                  "AND read_at IS NULL AND archived=0", (self._now(), tenant_id))
        return cur.rowcount

    def create_view(self, tenant_id: str, name: str, filters: dict[str, Any],
                    shared: bool = False, pinned: bool = False) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("name is required")
        allowed = {"query", "status", "tag", "min_total", "max_total", "missing"}
        if set(filters) - allowed:
            raise ValueError("unsupported filter")
        vid, now = str(uuid.uuid4()), self._now()
        with self.db:
            self.db.execute("INSERT INTO saved_views VALUES(?,?,?,?,?,?,?)",
                            (vid, tenant_id, name.strip(), json.dumps(filters, sort_keys=True),
                             int(shared), int(pinned), now))
        return {"view_id": vid, "name": name.strip(), "filters": filters,
                "shared": shared, "pinned": pinned, "created_at": now}

    def views(self, tenant_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM saved_views WHERE tenant_id=? "
                               "ORDER BY pinned DESC,name", (tenant_id,)).fetchall()
        return [{**dict(row), "filters": json.loads(row["filters"]),
                 "shared": bool(row["shared"]), "pinned": bool(row["pinned"])} for row in rows]

    def delete_view(self, tenant_id: str, view_id: str) -> bool:
        with self.db:
            cur = self.db.execute("DELETE FROM saved_views WHERE tenant_id=? AND view_id=?",
                                  (tenant_id, view_id))
        return cur.rowcount == 1

    def create_rule(self, tenant_id: str, name: str, conditions: dict[str, Any],
                    actions: dict[str, Any], priority: int = 100) -> dict[str, Any]:
        supported_conditions = {"vendor_contains", "currency", "min_total", "max_total"}
        supported_actions = {"tags", "project", "cost_center", "request_approval"}
        if not name.strip() or set(conditions) - supported_conditions or set(actions) - supported_actions:
            raise ValueError("invalid rule")
        rid, now = str(uuid.uuid4()), self._now()
        with self.db:
            self.db.execute("INSERT INTO automation_rules VALUES(?,?,?,?,?,?,1,?)",
                            (rid, tenant_id, name.strip(), json.dumps(conditions),
                             json.dumps(actions), priority, now))
        return {"rule_id": rid, "name": name.strip(), "conditions": conditions,
                "actions": actions, "priority": priority, "active": True}

    def rules(self, tenant_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM automation_rules WHERE tenant_id=? "
                               "ORDER BY priority,name", (tenant_id,)).fetchall()
        return [{**dict(row), "conditions": json.loads(row["conditions"]),
                 "actions": json.loads(row["actions"]), "active": bool(row["active"])}
                for row in rows]

    @staticmethod
    def _matches(payload: dict[str, Any], conditions: dict[str, Any]) -> bool:
        vendor = str(payload.get("vendor") or "").lower()
        total = float(payload.get("total") or 0)
        currency = str(payload.get("currency") or "").upper()
        return not any((
            conditions.get("vendor_contains") and
            str(conditions["vendor_contains"]).lower() not in vendor,
            conditions.get("currency") and str(conditions["currency"]).upper() != currency,
            conditions.get("min_total") is not None and total < float(conditions["min_total"]),
            conditions.get("max_total") is not None and total > float(conditions["max_total"]),
        ))

    def matching_rules(self, tenant_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return [rule for rule in self.rules(tenant_id)
                if rule["active"] and self._matches(payload, rule["conditions"])]

    def apply_rules(self, actor: Any, receipt_id: str, payload: dict[str, Any]) -> list[str]:
        applied = []
        for rule in self.matching_rules(actor.tenant_id, payload):
            actions = rule["actions"]
            self.service.set_metadata(actor, receipt_id, actions.get("tags", []),
                                      actions.get("project"), actions.get("cost_center"))
            if actions.get("request_approval"):
                self.service.request_approval(actor, receipt_id)
            applied.append(rule["rule_id"])
        return applied

    def rule_preview(self, tenant_id: str, conditions: dict[str, Any]) -> int:
        rows = self.db.execute("SELECT payload FROM receipts WHERE tenant_id=?", (tenant_id,)).fetchall()
        return sum(self._matches(json.loads(row["payload"]), conditions) for row in rows)

    def history(self, tenant_id: str, subject_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM activity_history WHERE tenant_id=? "
                               "AND subject_id=? ORDER BY created_at DESC",
                               (tenant_id, subject_id)).fetchall()
        return [{**dict(row), "before": json.loads(row["before_json"]) if row["before_json"] else None,
                 "after": json.loads(row["after_json"]) if row["after_json"] else None}
                for row in rows]

    def record_history(self, actor: Any, subject_id: str, action: str,
                       before: Any = None, after: Any = None) -> None:
        with self.db:
            self.db.execute("INSERT INTO activity_history VALUES(?,?,?,?,?,?,?,?)",
                            (str(uuid.uuid4()), actor.tenant_id, subject_id, action,
                             json.dumps(before, sort_keys=True) if before is not None else None,
                             json.dumps(after, sort_keys=True) if after is not None else None,
                             actor.role, self._now()))

    def duplicates(self, actor: Any) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT receipt_id,payload FROM receipts WHERE tenant_id=?",
                               (actor.tenant_id,)).fetchall()
        decided = {(r["left_id"], r["right_id"]) for r in self.db.execute(
            "SELECT left_id,right_id FROM duplicate_decisions WHERE tenant_id=?", (actor.tenant_id,))}
        result = []
        for index, left in enumerate(rows):
            a = json.loads(left["payload"])
            for right in rows[index + 1:]:
                pair = tuple(sorted((left["receipt_id"], right["receipt_id"])))
                if pair in decided:
                    continue
                b = json.loads(right["payload"])
                vendor_a = re.sub(r"\W+", "", str(a.get("vendor") or "").lower())
                vendor_b = re.sub(r"\W+", "", str(b.get("vendor") or "").lower())
                vendor_match = bool(vendor_a and vendor_b and
                                    (vendor_a in vendor_b or vendor_b in vendor_a))
                total_match = a.get("total") is not None and b.get("total") is not None and round(float(a["total"]), 2) == round(float(b["total"]), 2)
                date_match = bool(a.get("date") and a.get("date") == b.get("date"))
                score = (int(vendor_match) + int(total_match) + int(date_match)) / 3
                if total_match and vendor_match:
                    result.append({"left_id": pair[0], "right_id": pair[1],
                                   "left": a, "right": b, "confidence": round(score, 2),
                                   "evidence": {"vendor": vendor_match, "total": total_match,
                                                "date": date_match}})
        return result

    def decide_duplicate(self, tenant_id: str, left_id: str, right_id: str,
                         decision: str) -> dict[str, Any]:
        if decision not in {"same", "different"}:
            raise ValueError("invalid duplicate decision")
        left_id, right_id = sorted((left_id, right_id))
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO duplicate_decisions VALUES(?,?,?,?,?,?)",
                            (str(uuid.uuid4()), tenant_id, left_id, right_id, decision, self._now()))
        return {"left_id": left_id, "right_id": right_id, "decision": decision}

    def preferences(self, tenant_id: str, role: str) -> dict[str, Any]:
        row = self.db.execute("SELECT payload FROM user_preferences WHERE tenant_id=? AND role=?",
                              (tenant_id, role)).fetchone()
        return json.loads(row[0]) if row else {"language": "hu", "compact": False,
                                               "high_contrast": False,
                                               "dashboard_widgets": ["kpis", "actions", "spending", "quality"]}

    def save_preferences(self, tenant_id: str, role: str, payload: dict[str, Any]) -> dict[str, Any]:
        allowed = {"language", "compact", "high_contrast", "dashboard_widgets",
                   "onboarding_done", "email_alerts"}
        clean = {key: value for key, value in payload.items() if key in allowed}
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO user_preferences VALUES(?,?,?,?)",
                            (tenant_id, role, json.dumps(clean, sort_keys=True), self._now()))
        return clean

    def record_export(self, tenant_id: str, format: str, requested: int,
                      exported: int, errors: list[str]) -> dict[str, Any]:
        run_id, now = str(uuid.uuid4()), self._now()
        status = "completed" if not errors else ("partial" if exported else "failed")
        with self.db:
            self.db.execute("INSERT INTO export_runs VALUES(?,?,?,?,?,?,?,?)",
                            (run_id, tenant_id, format, status, requested, exported,
                             json.dumps(errors), now))
        return {"run_id": run_id, "format": format, "status": status,
                "requested": requested, "exported": exported, "errors": errors,
                "created_at": now}

    def exports(self, tenant_id: str) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT * FROM export_runs WHERE tenant_id=? "
                               "ORDER BY created_at DESC", (tenant_id,)).fetchall()
        return [{**dict(row), "errors": json.loads(row["errors"])} for row in rows]
