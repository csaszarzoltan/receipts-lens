"""Verify UX startup migrations on a private backup; never modify the source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pickle
import sqlite3
import tempfile
from pathlib import Path

from app.advanced_workspace import AdvancedWorkspace
from app.product_service import ProductService


def quoted(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def snapshot(db: sqlite3.Connection) -> dict[str, tuple[list[str], str, int]]:
    result = {}
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (name,) in tables:
        if name.startswith("sqlite_") or name in {"product_migrations", "upload_commands"}:
            continue
        columns = [row[1] for row in db.execute(f"PRAGMA table_info({quoted(name)})")]
        fields = ",".join(map(quoted, columns))
        digest = hashlib.sha256()
        count = 0
        for row in db.execute(f"SELECT {fields} FROM {quoted(name)}"):
            digest.update(pickle.dumps(tuple(row), protocol=4))
            count += 1
        result[name] = (columns, digest.hexdigest(), count)
    return result


def verify(source: Path) -> dict[str, object]:
    # Directory 0700 and database 0600. The only durable output is aggregate
    # verification evidence; no image, token, email or row content is logged.
    with tempfile.TemporaryDirectory(prefix="receiptlens-migration-") as folder:
        target = Path(folder) / "backup.sqlite"
        original = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True)
        copied = sqlite3.connect(target)
        try:
            original.backup(copied)
            os.chmod(target, 0o600)
            before = snapshot(copied)
        finally:
            copied.close()
            original.close()
        store = ProductService(target)
        try:
            AdvancedWorkspace(store)
            after = snapshot(store._db)
            unchanged = True
            for name, (columns, digest, count) in before.items():
                fields = ",".join(map(quoted, columns))
                actual = hashlib.sha256()
                rows = 0
                for row in store._db.execute(f"SELECT {fields} FROM {quoted(name)}"):
                    actual.update(pickle.dumps(tuple(row), protocol=4))
                    rows += 1
                unchanged &= actual.hexdigest() == digest and rows == count
            integrity = store._db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            migrated = (
                store._db.execute(
                    "SELECT COUNT(*) FROM product_migrations WHERE version='ux-upload-1'"
                ).fetchone()[0]
                == 1
            )
            command_table = "upload_commands" in {
                row[0]
                for row in store._db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            store._db.close()
            restarted = ProductService(target)
            try:
                repeated = snapshot(restarted._db) == after
            finally:
                restarted._db.close()
            report = {
                "source_access": "read-only",
                "private_copy_removed": True,
                "legacy_tables_checked": len(before),
                "receipts_preserved": before.get("receipts", ([], "", 0))[2],
                "legacy_rows_unchanged": unchanged,
                "integrity_ok": integrity,
                "migration_recorded_once": migrated,
                "upload_commands_created": command_table,
                "restart_preserves_data": repeated,
            }
            if not all((unchanged, integrity, migrated, command_table, repeated)):
                raise RuntimeError(
                    "Migration verification failed; details contain no personal data"
                )
            return report
        finally:
            store._db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.source), indent=2))
