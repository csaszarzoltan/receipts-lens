"""Tenant-safe tax categorization and deduction aggregation."""
from __future__ import annotations
import json,threading
from datetime import UTC,datetime
from typing import Any
from app.taxonomy import _TAX_RULES,TAX_CATEGORIES,labels
class TaxService:
 def __init__(self,service:Any)->None:
  self.db=service._db;self.lock=threading.RLock()
  with self.db:self.db.execute("CREATE TABLE IF NOT EXISTS receipt_tax(tenant_id TEXT,receipt_id TEXT,tax_category TEXT,tax_confidence TEXT,tax_locale TEXT,provenance TEXT,updated_at TEXT,PRIMARY KEY(tenant_id,receipt_id))")
 @staticmethod
 def categorize(vendor:str,line_items:list[dict[str,Any]],locale:str)->dict[str,Any]:
  locale=locale.upper()
  if locale not in TAX_CATEGORIES:raise ValueError("locale must be US or HU")
  text=" ".join([vendor]+[str(x.get("name") or "") for x in line_items]).lower()
  for keyword,category,loc in _TAX_RULES:
   if loc==locale and keyword in text:return {"tax_category":category,"confidence":"high","matched_rule":keyword}
  return {"tax_category":None,"confidence":"low","matched_rule":None}
 def override(self,tenant:str,rid:str,category:str,locale:str)->dict[str,Any]:
  locale=locale.upper()
  if category not in labels(locale):raise ValueError("unknown tax category")
  if not self.db.execute("SELECT 1 FROM receipts WHERE tenant_id=? AND receipt_id=?",(tenant,rid)).fetchone():raise KeyError(rid)
  now=datetime.now(UTC).isoformat()
  with self.lock,self.db:self.db.execute("INSERT OR REPLACE INTO receipt_tax VALUES(?,?,?,?,?,?,?)",(tenant,rid,category,"high",locale,"manual_override",now))
  return {"receipt_id":rid,"tax_category":category,"tax_locale":locale,"updated_at":now}
 def backfill(self,tenant:str,locale:str)->dict[str,int]:
  updated=skipped=0
  for row in self.db.execute("SELECT receipt_id,payload FROM receipts WHERE tenant_id=?",(tenant,)).fetchall():
   if self.db.execute("SELECT 1 FROM receipt_tax WHERE tenant_id=? AND receipt_id=?",(tenant,row["receipt_id"])).fetchone():skipped+=1;continue
   p=json.loads(row["payload"]);x=self.categorize(p.get("vendor","") ,p.get("line_items") or [],locale)
   if not x["tax_category"]:skipped+=1;continue
   with self.db:self.db.execute("INSERT INTO receipt_tax VALUES(?,?,?,?,?,?,?)",(tenant,row["receipt_id"],x["tax_category"],x["confidence"],locale.upper(),"rule:"+x["matched_rule"],datetime.now(UTC).isoformat()))
   updated+=1
  return {"updated":updated,"skipped":skipped}
 def deduction(self,tenant:str,year:int,locale:str)->dict[str,Any]:
  totals={}
  rows=self.db.execute("SELECT t.tax_category,r.payload FROM receipt_tax t JOIN receipts r ON r.receipt_id=t.receipt_id AND r.tenant_id=t.tenant_id WHERE t.tenant_id=? AND t.tax_locale=?",(tenant,locale.upper())).fetchall()
  for row in rows:
   p=json.loads(row["payload"])
   if str(p.get("date") or "")[:4]!=str(year):continue
   x=totals.setdefault(row["tax_category"],{"tax_category":row["tax_category"],"total":0.0,"count":0});x["total"]+=float(p.get("total") or 0);x["count"]+=1
  by=sorted(totals.values(),key=lambda x:x["tax_category"])
  for x in by:x["total"]=round(x["total"],2)
  grand=round(sum(x["total"] for x in by),2);return {"year":year,"locale":locale.upper(),"by_category":by,"grand_total":grand,"estimated_saving":round(grand*.25,2)}
