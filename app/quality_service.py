"""Persisted confidence calibration and benchmark metrics."""
from __future__ import annotations
import json, uuid
from datetime import UTC, datetime
from typing import Any
class QualityService:
 def __init__(self,service:Any)->None:
  self.db=service._db
  with self.db:self.db.executescript("""
  CREATE TABLE IF NOT EXISTS benchmark_reports(report_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,manifest_name TEXT NOT NULL,metrics_json TEXT NOT NULL,evaluated_count INTEGER NOT NULL,status TEXT NOT NULL,created_by_role TEXT NOT NULL,created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS confidence_profiles(profile_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,version INTEGER NOT NULL,thresholds_json TEXT NOT NULL,benchmark_report_id TEXT NOT NULL,active INTEGER NOT NULL,created_by_role TEXT NOT NULL,created_at TEXT NOT NULL);
  """)
 @staticmethod
 def now()->str:return datetime.now(UTC).isoformat()
 def evaluate(self,actor:Any,manifest_name:str,cases:list[dict[str,Any]])->dict[str,Any]:
  if actor.role!='admin':raise PermissionError
  if not manifest_name or not cases:raise ValueError('manifest_name and cases are required')
  fields=['vendor','date','total','tax','currency','line_items']; per={}; total=0
  for field in fields:
   counts={'true_clear':0,'false_clear':0,'true_review':0,'false_review':0}; evaluated=0
   for i,c in enumerate(cases):
    expected=c.get('expected',{}); predicted=c.get('predicted',{}); confidence=c.get('confidence',{})
    if field not in expected:continue
    evaluated+=1; correct=predicted.get(field)==expected.get(field); clear=float(confidence.get(field,0))>=.7
    counts['true_clear' if correct and clear else 'false_clear' if (not correct and clear) else 'true_review' if (not correct) else 'false_review']+=1
   if evaluated:
    counts['evaluated']=evaluated; counts['false_clear_rate']=counts['false_clear']/evaluated; per[field]=counts; total+=evaluated
  if not total:raise ValueError('benchmark contains zero labelled fields')
  rid=str(uuid.uuid4()); metrics={'fields':per,'evaluated_count':total}
  with self.db:self.db.execute('INSERT INTO benchmark_reports VALUES(?,?,?,?,?,?,?,?)',(rid,actor.tenant_id,manifest_name,json.dumps(metrics,sort_keys=True),total,'completed',actor.role,self.now()))
  return {'report_id':rid,**metrics,'status':'completed'}
 def report(self,tenant:str,rid:str)->dict[str,Any]:
  row=self.db.execute('SELECT * FROM benchmark_reports WHERE tenant_id=? AND report_id=?',(tenant,rid)).fetchone()
  if not row:raise KeyError(rid)
  return {'report_id':rid,'manifest_name':row['manifest_name'],**json.loads(row['metrics_json']),'status':row['status'],'created_at':row['created_at']}
 def publish(self,actor:Any,rid:str,thresholds:dict[str,float])->dict[str,Any]:
  if actor.role!='admin':raise PermissionError
  self.report(actor.tenant_id,rid)
  allowed={'vendor','date','total','tax','currency','line_items'}
  if not thresholds or set(thresholds)-allowed or any(not 0<=float(v)<=1 for v in thresholds.values()):raise ValueError('invalid thresholds')
  version=(self.db.execute('SELECT COALESCE(MAX(version),0)+1 FROM confidence_profiles WHERE tenant_id=?',(actor.tenant_id,)).fetchone()[0]); pid=str(uuid.uuid4())
  with self.db:
   self.db.execute('UPDATE confidence_profiles SET active=0 WHERE tenant_id=?',(actor.tenant_id,))
   self.db.execute('INSERT INTO confidence_profiles VALUES(?,?,?,?,?,1,?,?)',(pid,actor.tenant_id,version,json.dumps(thresholds,sort_keys=True),rid,actor.role,self.now()))
  return {'profile_id':pid,'version':version,'thresholds':thresholds,'benchmark_report_id':rid,'active':True}
 def active(self,tenant:str)->dict[str,Any]|None:
  row=self.db.execute('SELECT * FROM confidence_profiles WHERE tenant_id=? AND active=1 ORDER BY version DESC LIMIT 1',(tenant,)).fetchone()
  return None if not row else {'profile_id':row['profile_id'],'version':row['version'],'thresholds':json.loads(row['thresholds_json']),'benchmark_report_id':row['benchmark_report_id'],'active':True}
