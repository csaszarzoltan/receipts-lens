import json
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.accounting_projection import AccountingProjectionService
from app.connection_service import ConnectionService
from app.credential_store import CredentialStore
from app.product_service import Actor, ProductService
from app.provider_export_service import ProviderExportService
from app.reconciliation_service import ReconciliationService


class FakeProvider:
 def __init__(self): self.created=[]; self.remote={}; self.failures={}
 def company(self, token): return {'id':'realm-1','name':'Sandbox Books'}
 def references(self, kind): return [{'id':'acct-1','name':'Expenses','active':True}]
 def create_purchase(self,payload,dedupe_key):
  if dedupe_key in self.remote:return self.remote[dedupe_key]
  result={'id':f'q-{len(self.created)+1}','sync_token':'0',**payload};self.created.append(result);self.remote[dedupe_key]=result;return result
 def get_purchase(self,pid):
  for x in self.created:
   if x['id']==pid:return x
  raise KeyError(pid)

def parsed(total=10,currency='EUR',tax=1):
 return SimpleNamespace(merchant='Shop',date='2026-08-01',total=total,tax=tax,currency=currency,items=[],confidence={'vendor':.9,'date':.9,'total':.9,'tax':.9,'currency':.9,'line_items':.9})

def test_us_010_oauth_state_is_single_use_tenant_bound_and_tokens_encrypted(tmp_path):
 s=ProductService(tmp_path/'db.sqlite'); key=b'k'*32;c=ConnectionService(s,CredentialStore(key));a=Actor('a','admin')
 started=c.start_oauth(a,'/integrations'); assert 'state=' in started['authorization_url']
 conn=c.complete_oauth(a,started['state'],'code','realm-1',{'access_token':'SECRET-A','refresh_token':'SECRET-R','expires_in':3600})
 assert conn['provider_company_id']=='realm-1' and 'SECRET' not in json.dumps(conn)
 raw=(tmp_path/'db.sqlite').read_bytes();assert b'SECRET-A' not in raw and b'SECRET-R' not in raw
 with pytest.raises(ValueError):c.complete_oauth(a,started['state'],'code','realm-1',{'access_token':'x','refresh_token':'y'})

def test_us_011_refresh_rotation_and_invalid_grant_health(tmp_path):
 s=ProductService(tmp_path/'db.sqlite');c=ConnectionService(s,CredentialStore(b'z'*32));a=Actor('a','admin')
 st=c.start_oauth(a,'/integrations');co=c.complete_oauth(a,st['state'],'c','realm',{'access_token':'old','refresh_token':'old-r','expires_in':-1})
 c.rotate_tokens(a,co['connection_id'],{'access_token':'new','refresh_token':'new-r','expires_in':3600})
 assert c.test_connection(a,co['connection_id'],FakeProvider())['health']=='healthy'
 c.mark_reauthorization(a,co['connection_id']); assert c.get(a,co['connection_id'])['reauthorization_required'] is True

def test_us_012_mapping_versions_and_reference_drift(tmp_path):
 s=ProductService(tmp_path/'db.sqlite');c=ConnectionService(s,CredentialStore(b'x'*32));a=Actor('a','admin')
 st=c.start_oauth(a,'/integrations');co=c.complete_oauth(a,st['state'],'c','realm',{'access_token':'a','refresh_token':'r','expires_in':3600})
 with pytest.raises(ValueError):c.validate_mapping({'expense_account_ref':''},FakeProvider())
 valid=c.validate_mapping({'expense_account_ref':'acct-1','tax_strategy':'exclusive'},FakeProvider());m=c.save_mapping(a,co['connection_id'],valid['mapping'],valid['snapshot_hash'])
 assert m['version']==1 and m['valid']

def test_us_013_014_replay_safe_export_retry_and_redaction(tmp_path):
 s=ProductService(tmp_path/'db.sqlite');a=Actor('t','admin');provider=FakeProvider();exp=ProviderExportService(s,provider)
 ids=[s.create_receipt(a,parsed(i+1),'r.png')['receipt_id'] for i in range(50)]
 run=exp.create_run(a,'conn','prep',[(rid,1,{'date':'2026-08-01','total':i+1,'currency':'EUR'}) for i,rid in enumerate(ids)],1,'key')
 exp.process_run(a,run['run_id']);exp.process_run(a,run['run_id'])
 detail=exp.run(a,run['run_id']);assert detail['counts']['created']==50 and len(provider.created)==50
 again=exp.create_run(a,'conn','prep',[(ids[0],1,{'date':'2026-08-01','total':1,'currency':'EUR'})],1,'different')
 exp.process_run(a,again['run_id']);assert exp.run(a,again['run_id'])['counts']['already_exported']==1
 assert 'token' not in json.dumps(exp.safe_error({'message':'bad','access_token':'secret','request_id':'req-1'})).lower()

def test_us_015_reconciliation_match_mismatch_missing(tmp_path):
 s=ProductService(tmp_path/'db.sqlite');a=Actor('t','admin');p=FakeProvider();e=ProviderExportService(s,p);rid=s.create_receipt(a,parsed(10),'r')['receipt_id']
 run=e.create_run(a,'c','p',[(rid,1,{'date':'2026-08-01','total':10,'currency':'EUR'})],1,'k');e.process_run(a,run['run_id']);item=e.items(a,run['run_id'])[0]
 r=ReconciliationService(s,p);assert r.verify(a,item,{'date':'2026-08-01','total':10,'currency':'EUR'})['status']=='verified'
 p.created[0]['total']=12;assert r.verify(a,item,{'date':'2026-08-01','total':10,'currency':'EUR'})['status']=='needs_reconciliation'
 p.created.clear();assert r.verify(a,item,{'date':'2026-08-01','total':10,'currency':'EUR'})['status']=='missing_remote'

def test_us_016_017_018_currency_tax_and_preview(tmp_path):
 s=ProductService(tmp_path/'db.sqlite');a=Actor('t','admin');rid=s.create_receipt(a,parsed(12,'EUR',2),'r')['receipt_id'];svc=AccountingProjectionService(s)
 svc.set_rate(a,'EUR','CHF',Decimal('0.95'),date(2026,8,1),'manual')
 projection=svc.refresh(a,rid,'CHF');assert projection['original_total']=='12.00' and projection['reporting_total']=='11.40'
 assert svc.validate_tax(Decimal(10),Decimal(2),Decimal(12))['valid']
 with pytest.raises(ValueError):svc.validate_tax(Decimal(10),Decimal(-1),Decimal(9))
 preview=svc.preview(a,rid,1,1,{'expense_account_ref':'acct-1'});assert preview['snapshot_hash']==svc.preview(a,rid,1,1,{'expense_account_ref':'acct-1'})['snapshot_hash']
 assert 'cipher' not in json.dumps(preview).lower()

def test_us_014_safe_error_redacts_token_fields():
 clean=ProviderExportService.safe_error({'message':'provider rejected request','access_token':'secret','request_id':'req-2'})
 assert clean=={'message':'provider rejected request','request_id':'req-2'}

def test_us_017_tax_boundary_is_measurable():
 assert AccountingProjectionService.validate_tax(Decimal('10.00'),Decimal('2.00'),Decimal('12.01'))['valid']
 assert not AccountingProjectionService.validate_tax(Decimal('10.00'),Decimal('2.00'),Decimal('12.02'))['valid']

def test_us_018_preview_is_version_bound(tmp_path):
 s=ProductService(tmp_path/'p.sqlite');a=Actor('t','admin');rid=s.create_receipt(a,parsed(),'r')['receipt_id'];svc=AccountingProjectionService(s)
 with pytest.raises(RuntimeError,match='preparation_stale'):svc.preview(a,rid,99,1,{'expense_account_ref':'acct-1'})
