"""Durable replay-safe provider export run and item workflow."""
from __future__ import annotations
import hashlib,json,uuid
from datetime import UTC,datetime
class ProviderExportService:
 def __init__(self,service,provider):
  self.db,self.provider=service._db,provider
  with self.db:self.db.executescript('''CREATE TABLE IF NOT EXISTS provider_export_runs(run_id TEXT PRIMARY KEY,tenant_id TEXT,connection_id TEXT,preparation_id TEXT,command_key TEXT,status TEXT,created_at TEXT,UNIQUE(tenant_id,command_key));CREATE TABLE IF NOT EXISTS provider_export_items(item_id TEXT PRIMARY KEY,run_id TEXT,tenant_id TEXT,receipt_id TEXT,receipt_version INTEGER,mapping_version INTEGER,dedupe_key TEXT,status TEXT,attempt_count INTEGER,payload_json TEXT,provider_id TEXT,provider_sync_token TEXT,safe_error_json TEXT);CREATE TABLE IF NOT EXISTS provider_links(tenant_id TEXT,connection_id TEXT,receipt_id TEXT,receipt_version INTEGER,provider_id TEXT,provider_sync_token TEXT,UNIQUE(tenant_id,connection_id,receipt_id,receipt_version));''')
 def create_run(self,actor,connection_id,preparation_id,items,mapping_version,command_key):
  old=self.db.execute('SELECT run_id FROM provider_export_runs WHERE tenant_id=? AND command_key=?',(actor.tenant_id,command_key)).fetchone()
  if old:return {'run_id':old[0],'status':'queued'}
  rid=str(uuid.uuid4());now=datetime.now(UTC).isoformat()
  with self.db:
   self.db.execute('INSERT INTO provider_export_runs VALUES(?,?,?,?,?,"queued",?)',(rid,actor.tenant_id,connection_id,preparation_id,command_key,now))
   for receipt_id,version,payload in items:
    d=hashlib.sha256(f'{actor.tenant_id}|{connection_id}|{receipt_id}|{version}|{mapping_version}|purchase'.encode()).hexdigest()
    self.db.execute('INSERT INTO provider_export_items VALUES(?,?,?,?,?,?,?,"queued",0,?,?,?,NULL)',(str(uuid.uuid4()),rid,actor.tenant_id,receipt_id,version,mapping_version,d,json.dumps(payload,sort_keys=True),None,None))
  return {'run_id':rid,'status':'queued'}
 def process_run(self,actor,run_id):
  run=self.db.execute('SELECT * FROM provider_export_runs WHERE tenant_id=? AND run_id=?',(actor.tenant_id,run_id)).fetchone()
  if not run:raise KeyError(run_id)
  rows=self.db.execute('SELECT * FROM provider_export_items WHERE run_id=? AND status="queued"',(run_id,)).fetchall()
  for r in rows:
   old=self.db.execute('SELECT * FROM provider_links WHERE tenant_id=? AND connection_id=? AND receipt_id=? AND receipt_version=?',(actor.tenant_id,run['connection_id'],r['receipt_id'],r['receipt_version'])).fetchone()
   if old:
    with self.db:self.db.execute('UPDATE provider_export_items SET status="already_exported",provider_id=?,provider_sync_token=? WHERE item_id=?',(old['provider_id'],old['provider_sync_token'],r['item_id']));continue
   try:
    result=self.provider.create_purchase(json.loads(r['payload_json']),r['dedupe_key'])
    with self.db:
     self.db.execute('UPDATE provider_export_items SET status="created",attempt_count=attempt_count+1,provider_id=?,provider_sync_token=? WHERE item_id=?',(result['id'],result.get('sync_token'),r['item_id']))
     self.db.execute('INSERT OR IGNORE INTO provider_links VALUES(?,?,?,?,?,?)',(actor.tenant_id,run['connection_id'],r['receipt_id'],r['receipt_version'],result['id'],result.get('sync_token')))
   except Exception as exc:
    with self.db:self.db.execute('UPDATE provider_export_items SET status="failed",attempt_count=attempt_count+1,safe_error_json=? WHERE item_id=?',(json.dumps(self.safe_error({'message':str(exc)})),r['item_id']))
  with self.db:self.db.execute('UPDATE provider_export_runs SET status="completed" WHERE run_id=?',(run_id,))
 def items(self,actor,run_id):return [dict(x) for x in self.db.execute('SELECT * FROM provider_export_items WHERE tenant_id=? AND run_id=? ORDER BY rowid',(actor.tenant_id,run_id)).fetchall()]
 def run(self,actor,run_id):
  r=self.db.execute('SELECT * FROM provider_export_runs WHERE tenant_id=? AND run_id=?',(actor.tenant_id,run_id)).fetchone()
  if not r:raise KeyError(run_id)
  counts={k:0 for k in ['created','already_exported','failed','queued']}
  for x in self.items(actor,run_id):counts[x['status']]=counts.get(x['status'],0)+1
  return {**dict(r),'counts':counts,'items':self.items(actor,run_id)}
 @staticmethod
 def safe_error(error):
  clean={'message':str(error.get('message','provider error'))[:1800]}
  if error.get('request_id'):clean['request_id']=error['request_id']
  return clean
