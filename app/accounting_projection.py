"""Decimal source-currency, tax and deterministic preview projections."""
from __future__ import annotations
import hashlib,json
from datetime import date
from decimal import Decimal,ROUND_HALF_UP
from typing import Any
class AccountingProjectionService:
 def __init__(self,service:Any):
  self.db=service._db
  with self.db:self.db.executescript('''CREATE TABLE IF NOT EXISTS projection_rates(tenant_id TEXT,base TEXT,quote TEXT,rate TEXT,rate_date TEXT,source TEXT,PRIMARY KEY(tenant_id,base,quote,rate_date));CREATE TABLE IF NOT EXISTS receipt_accounting_projections(tenant_id TEXT,receipt_id TEXT PRIMARY KEY,receipt_version INTEGER,payload_json TEXT,stale INTEGER,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);''')
 def set_rate(self,actor,base,quote,rate:Decimal,rate_date:date,source):
  if rate<=0:raise ValueError('rate must be positive')
  with self.db:self.db.execute('INSERT OR REPLACE INTO projection_rates VALUES(?,?,?,?,?,?)',(actor.tenant_id,base,quote,str(rate),rate_date.isoformat(),source))
 def refresh(self,actor,rid,reporting_currency):
  row=self.db.execute('SELECT payload,version FROM receipts WHERE tenant_id=? AND receipt_id=?',(actor.tenant_id,rid)).fetchone()
  if not row:raise KeyError(rid)
  src=json.loads(row['payload']);base=src.get('currency');total=Decimal(str(src.get('total')))
  if base==reporting_currency:rate=Decimal('1');source='identity';rdate=src.get('date')
  else:
   rr=self.db.execute('SELECT rate,rate_date,source FROM projection_rates WHERE tenant_id=? AND base=? AND quote=? AND rate_date<=? ORDER BY rate_date DESC LIMIT 1',(actor.tenant_id,base,reporting_currency,src.get('date'))).fetchone()
   if not rr:raise KeyError('exchange_rate_missing')
   rate=Decimal(rr['rate']);rdate=rr['rate_date'];source=rr['source']
  out={'original_currency':base,'original_total':f'{total:.2f}','reporting_currency':reporting_currency,'reporting_total':f'{(total*rate).quantize(Decimal("0.01"),rounding=ROUND_HALF_UP):.2f}','rate':str(rate),'rate_date':rdate,'source':source,'receipt_version':row['version'],'stale':False}
  with self.db:self.db.execute('INSERT OR REPLACE INTO receipt_accounting_projections(tenant_id,receipt_id,receipt_version,payload_json,stale) VALUES(?,?,?,?,0)',(actor.tenant_id,rid,row['version'],json.dumps(out,sort_keys=True)))
  return out
 @staticmethod
 def validate_tax(net:Decimal,tax:Decimal,gross:Decimal):
  if min(net,tax,gross)<0 or tax>gross:raise ValueError('tax_arithmetic_invalid')
  delta=abs(net+tax-gross);return {'valid':delta<=Decimal('.01'),'delta':str(delta)}
 def preview(self,actor,rid,receipt_version,mapping_version,mapping):
  row=self.db.execute('SELECT payload FROM receipts WHERE tenant_id=? AND receipt_id=? AND version=?',(actor.tenant_id,rid,receipt_version)).fetchone()
  if not row:raise RuntimeError('preparation_stale')
  p=json.loads(row[0]);body={'receipt_id':rid,'receipt_version':receipt_version,'mapping_version':mapping_version,'date':p.get('date'),'currency':p.get('currency'),'total':p.get('total'),'vendor':p.get('vendor'),'account_ref':mapping.get('expense_account_ref'),'attachment_filename':'receipt'}
  body['snapshot_hash']=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest();return body
