"""Versioned, repeatable migrations for the product data store."""

import sqlite3


def migrate_upload_commands(db: sqlite3.Connection) -> None:
    with db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("CREATE TABLE IF NOT EXISTS product_migrations (version TEXT PRIMARY KEY)")
        if db.execute("SELECT 1 FROM product_migrations WHERE version='ux-upload-1'").fetchone():
            return
        db.execute("""CREATE TABLE IF NOT EXISTS upload_commands (
            tenant_id TEXT NOT NULL, command_key TEXT NOT NULL,
            fingerprint TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY (tenant_id, command_key))""")
        db.execute("INSERT INTO product_migrations VALUES ('ux-upload-1')")
