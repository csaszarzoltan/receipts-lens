"""Idempotent, tenant-safe accounting export workflow."""
from __future__ import annotations
import csv, io, json, sqlite3, uuid
from datetime import UTC, datetime
from typing import Any

class ExportWorkflow:
    def __init__(self, service: Any, accounting: Any) -> None:
        self.service, self.accounting, self.db = service, accounting, service._db
        with self.db:
            self.db.executescript("""
            CREATE TABLE IF NOT EXISTS export_commands(
              command_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, preparation_id TEXT NOT NULL,
              idempotency_key TEXT NOT NULL, warning_ack_json TEXT NOT NULL, run_id TEXT NOT NULL,
              response_json TEXT NOT NULL, artifact TEXT, created_at TEXT NOT NULL,
              UNIQUE(tenant_id,idempotency_key));
            """)
            self._ensure_column("export_preparations", "receipt_versions", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column("export_preparations", "validation_snapshot", "TEXT NOT NULL DEFAULT '{}'")
    def _ensure_column(self, table: str, name: str, declaration: str) -> None:
        columns={r[1] for r in self.db.execute(f"PRAGMA table_info({table})")}
        if name not in columns: self.db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {declaration}")
    @staticmethod
    def now()->str: return datetime.now(UTC).isoformat()
    def prepare(self, actor: Any, receipt_ids:list[str], connection_id:str|None)->dict[str,Any]:
        if not 1 <= len(receipt_ids) <= 200: raise ValueError("receipt_ids must contain 1 to 200 items")
        unique=list(dict.fromkeys(receipt_ids)); result=self.accounting.prepare_export(actor,unique,connection_id)
        versions={}; snapshot={}
        for rid in unique:
            row=self.db.execute("SELECT version FROM receipts WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid)).fetchone()
            if row:
                versions[rid]=row[0]
                snapshot[rid]=self.accounting.validate(actor,rid,connection_id)
        with self.db:
            self.db.execute("UPDATE export_preparations SET receipt_versions=?,validation_snapshot=? WHERE preparation_id=? AND tenant_id=?",
                (json.dumps(versions,sort_keys=True),json.dumps(snapshot,sort_keys=True),result['preparation_id'],actor.tenant_id))
        return {**result,"receipt_versions":versions,"validation_snapshot":snapshot}
    def execute(self,actor:Any,preparation_id:str,acknowledged:list[str],idempotency_key:str)->dict[str,Any]:
        if not idempotency_key.strip(): raise ValueError("Idempotency-Key is required")
        old=self.db.execute("SELECT response_json FROM export_commands WHERE tenant_id=? AND idempotency_key=?",(actor.tenant_id,idempotency_key)).fetchone()
        if old:return json.loads(old[0])
        row=self.db.execute("SELECT * FROM export_preparations WHERE tenant_id=? AND preparation_id=?",(actor.tenant_id,preparation_id)).fetchone()
        if not row: raise KeyError(preparation_id)
        valid=json.loads(row['valid_ids']); warnings=json.loads(row['warnings']); versions=json.loads(row['receipt_versions'] or '{}')
        warning_ids={x['receipt_id'] for x in warnings}
        if warning_ids-set(acknowledged): raise ValueError("all warning receipts must be acknowledged")
        for rid,version in versions.items():
            current=self.db.execute("SELECT version FROM receipts WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid)).fetchone()
            if current and current[0]!=version: raise RuntimeError("preparation is stale")
        output=io.StringIO(); writer=csv.writer(output); writer.writerow(['receipt_id','vendor','date','total','currency'])
        for rid in valid:
            r=self.db.execute("SELECT payload FROM receipts WHERE tenant_id=? AND receipt_id=?",(actor.tenant_id,rid)).fetchone()
            if r:
                p=json.loads(r[0]); writer.writerow([rid,p.get('vendor'),p.get('date'),p.get('total'),p.get('currency')])
        run_id=str(uuid.uuid4()); response={"run_id":run_id,"status":"completed","preparation_id":preparation_id,"requested":len(versions),"exported":len(valid),"error_code":None,"retryable":False}
        with self.db:
            self.db.execute("INSERT INTO export_commands VALUES(?,?,?,?,?,?,?,?,?)",(str(uuid.uuid4()),actor.tenant_id,preparation_id,idempotency_key,json.dumps(sorted(set(acknowledged))),run_id,json.dumps(response),output.getvalue(),self.now()))
        return response
    def run(self,tenant:str,run_id:str)->dict[str,Any]:
        row=self.db.execute("SELECT response_json,created_at FROM export_commands WHERE tenant_id=? AND run_id=?",(tenant,run_id)).fetchone()
        if not row: raise KeyError(run_id)
        return {**json.loads(row[0]),"created_at":row[1]}
    def artifact(self,tenant:str,run_id:str)->str:
        row=self.db.execute("SELECT artifact FROM export_commands WHERE tenant_id=? AND run_id=?",(tenant,run_id)).fetchone()
        if not row: raise KeyError(run_id)
        return row[0]
