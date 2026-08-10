"""Versioned, previewable and reversible receipt automation."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any


class AutomationService:
 def __init__(self,service:Any,advanced:Any)->None:
  self.service,self.advanced,self.db=service,advanced,service._db
  with self.db:self.db.executescript("""
  CREATE TABLE IF NOT EXISTS automation_rule_versions(rule_id TEXT NOT NULL,tenant_id TEXT NOT NULL,version INTEGER NOT NULL,status TEXT NOT NULL,name TEXT NOT NULL,conditions_json TEXT NOT NULL,actions_json TEXT NOT NULL,priority INTEGER NOT NULL,preview_token TEXT,previewed_at TEXT,created_by_role TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(rule_id,version));
  CREATE TABLE IF NOT EXISTS automation_runs(run_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,rule_id TEXT NOT NULL,rule_version INTEGER NOT NULL,status TEXT NOT NULL,input_json TEXT NOT NULL,summary_json TEXT NOT NULL,rollback_of TEXT,created_by_role TEXT NOT NULL,created_at TEXT NOT NULL,completed_at TEXT);
  CREATE TABLE IF NOT EXISTS automation_run_items(run_id TEXT NOT NULL,receipt_id TEXT NOT NULL,before_json TEXT NOT NULL,after_json TEXT NOT NULL,before_version INTEGER NOT NULL,after_version INTEGER NOT NULL,status TEXT NOT NULL,error_code TEXT,PRIMARY KEY(run_id,receipt_id));
  """)
 @staticmethod
 def now()->str:return datetime.now(UTC).isoformat()
 def create(self,actor:Any,name:str,conditions:dict,actions:dict,priority:int)->dict:
  if not 0<=priority<=1000:raise ValueError('priority must be between 0 and 1000')
  self.advanced.create_rule(actor.tenant_id,name,conditions,actions,priority)
  rid=str(uuid.uuid4()); now=self.now()
  with self.db:self.db.execute('INSERT INTO automation_rule_versions VALUES(?,?,1,?,?,?,?,?,NULL,NULL,?,?)',(rid,actor.tenant_id,'draft',name,json.dumps(conditions),json.dumps(actions),priority,actor.role,now))
  return {'rule_id':rid,'version':1,'status':'draft','name':name,'conditions':conditions,'actions':actions,'priority':priority}
 def _rule(self,tenant:str,rid:str,version:int|None=None):
  q='SELECT * FROM automation_rule_versions WHERE tenant_id=? AND rule_id=?'; args=[tenant,rid]
  if version is not None:q+=' AND version=?';args.append(version)
  q+=' ORDER BY version DESC LIMIT 1'; row=self.db.execute(q,args).fetchone()
  if not row:raise KeyError(rid)
  return row
 def preview(self,actor:Any,rid:str,version:int,receipt_ids:list[str]|None=None)->dict:
  rule=self._rule(actor.tenant_id,rid,version); conditions=json.loads(rule['conditions_json']); actions=json.loads(rule['actions_json'])
  rows=self.db.execute('SELECT receipt_id,payload FROM receipts WHERE tenant_id=?',(actor.tenant_id,)).fetchall(); matches=[]; conflicts=[]
  active=self.db.execute("SELECT * FROM automation_rule_versions WHERE tenant_id=? AND status='active' AND NOT(rule_id=? AND version=?) ORDER BY priority,created_at,rule_id",(actor.tenant_id,rid,version)).fetchall()
  target_fields={'tags','project','cost_center','request_approval'}
  for row in rows:
   if receipt_ids and row['receipt_id'] not in receipt_ids:continue
   payload=json.loads(row['payload'])
   if not self.advanced._matches(payload,conditions):continue
   matches.append(row['receipt_id'])
   candidates=[{'rule_id':rid,'version':version,'priority':rule['priority'],'created_at':rule['created_at'],'actions':actions}]
   for other in active:
    if self.advanced._matches(payload,json.loads(other['conditions_json'])):
     candidates.append({'rule_id':other['rule_id'],'version':other['version'],'priority':other['priority'],'created_at':other['created_at'],'actions':json.loads(other['actions_json'])})
   candidates.sort(key=lambda x:(x['priority'],x['created_at'],x['rule_id']))
   for field in target_fields:
    values=[(c,c['actions'][field]) for c in candidates if field in c['actions']]
    if len({json.dumps(v,sort_keys=True) for _,v in values})>1:
     winner=values[0][0]
     conflicts.append({'receipt_id':row['receipt_id'],'field':field,'winner_rule_id':winner['rule_id'],'winner_value':winner['actions'][field],
                       'candidates':[{'rule_id':c['rule_id'],'priority':c['priority'],'value':v} for c,v in values]})
  token=str(uuid.uuid4())
  with self.db:self.db.execute('UPDATE automation_rule_versions SET preview_token=?,previewed_at=? WHERE rule_id=? AND version=?',(token,self.now(),rid,version))
  return {'preview_token':token,'match_count':len(matches),'samples':matches[:20],'conflicts':conflicts}
 def activate(self,actor:Any,rid:str,version:int,token:str)->dict:
  r=self._rule(actor.tenant_id,rid,version)
  if not r['preview_token'] or r['preview_token']!=token:raise ValueError('a current successful preview is required')
  with self.db:self.db.execute("UPDATE automation_rule_versions SET status='active' WHERE tenant_id=? AND rule_id=? AND version=?",(actor.tenant_id,rid,version))
  return {'rule_id':rid,'version':version,'status':'active'}
 def run(self,actor:Any,rid:str,version:int,receipt_ids:list[str])->dict:
  r=self._rule(actor.tenant_id,rid,version); actions=json.loads(r['actions_json']); runid=str(uuid.uuid4());done=0
  with self.db:
   self.db.execute('INSERT INTO automation_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)',(runid,actor.tenant_id,rid,version,'processing',json.dumps(receipt_ids),json.dumps({}),None,actor.role,self.now(),None))
   for receipt_id in receipt_ids:
    row=self.db.execute('SELECT payload,version FROM receipts WHERE tenant_id=? AND receipt_id=?',(actor.tenant_id,receipt_id)).fetchone()
    if not row:continue
    before=json.loads(row['payload']); after=dict(before); meta={k:v for k,v in actions.items() if k in {'tags','project','cost_center'}}
    if meta:self.service.set_metadata(actor,receipt_id,meta.get('tags',[]),meta.get('project'),meta.get('cost_center'))
    version_after=row['version']+1; self.db.execute('UPDATE receipts SET version=? WHERE receipt_id=?',(version_after,receipt_id))
    self.db.execute('INSERT INTO automation_run_items VALUES(?,?,?,?,?,?,?,NULL)',(runid,receipt_id,json.dumps(before),json.dumps(after),row['version'],version_after,'completed'));done+=1
   summary={'affected':done,'failed':len(receipt_ids)-done};self.db.execute("UPDATE automation_runs SET status='completed',summary_json=?,completed_at=? WHERE run_id=?",(json.dumps(summary),self.now(),runid))
  return {'run_id':runid,'status':'completed',**summary}
 def detail(self,tenant:str,runid:str)->dict:
  run=self.db.execute('SELECT * FROM automation_runs WHERE tenant_id=? AND run_id=?',(tenant,runid)).fetchone()
  if not run:raise KeyError(runid)
  items=[dict(x) for x in self.db.execute('SELECT * FROM automation_run_items WHERE run_id=?',(runid,)).fetchall()]
  return {'run_id':runid,'status':run['status'],'summary':json.loads(run['summary_json']),'items':items}
 def rollback_preview(self,tenant:str,runid:str)->dict:
  d=self.detail(tenant,runid);eligible=[];conflicts=[]
  for item in d['items']:
   row=self.db.execute('SELECT version FROM receipts WHERE tenant_id=? AND receipt_id=?',(tenant,item['receipt_id'])).fetchone()
   (eligible if row and row[0]==item['after_version'] else conflicts).append(item['receipt_id'])
  return {'eligible':eligible,'conflicts':conflicts}
 def rollback(self,actor:Any,runid:str,eligible:list[str],fail_after:int|None=None)->dict:
  preview=self.rollback_preview(actor.tenant_id,runid); allowed=[x for x in eligible if x in preview['eligible']]
  with self.db:
   for index,rid in enumerate(allowed):
    if fail_after is not None and index >= fail_after: raise sqlite3.OperationalError('injected rollback failure')
    item=self.db.execute('SELECT * FROM automation_run_items WHERE run_id=? AND receipt_id=?',(runid,rid)).fetchone()
    self.db.execute('UPDATE receipts SET payload=?,version=? WHERE tenant_id=? AND receipt_id=?',(item['before_json'],item['after_version']+1,actor.tenant_id,rid))
  return {'run_id':runid,'rolled_back':len(allowed),'conflicts':preview['conflicts']}
