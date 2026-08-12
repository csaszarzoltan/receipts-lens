import base64
import sqlite3
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.advanced_workspace import AdvancedWorkspace
from app.automation_service import AutomationService
from app.inbox_service import InboxService, safe_filename
from app.product_service import Actor, ProductService


def parsed(vendor='Coffee'):
 return SimpleNamespace(merchant=vendor,date='2026-08-01',total=10,tax=1,currency='CHF',items=[],confidence={'vendor':.5})
def png():return b'\x89PNG\r\n\x1a\n'+b'x'*20

def test_us_007_tracks_bytes_quarantine_retry_and_parent_status(tmp_path):
 s=ProductService(tmp_path/'db'); calls={'n':0}
 def processor(data,mime):calls['n']+=1; return 'receipt-1'
 inbox=InboxService(s,processor)
 result=inbox.receive('t','sender@example.com','Docs',[
  {'filename':'../receipt.png','content_type':'image/png','content_base64':base64.b64encode(png()).decode()},
  {'filename':'evil.exe','content_type':'application/octet-stream','content_base64':base64.b64encode(b'MZevil').decode()}])
 assert result['status']=='partial' and result['attachments'][0]['status']=='completed'
 assert result['attachments'][0]['filename']=='receipt.png' and result['attachments'][1]['status']=='quarantined'
 assert s._db.execute('select length(content) from inbound_email_attachments where status="completed"').fetchone()[0]==len(png())
 with pytest.raises(ValueError):inbox.retry('t',result['email_id'],result['attachments'][1]['attachment_id'])
 with pytest.raises(KeyError):inbox.get('other',result['email_id'])

def test_us_007_failed_attachment_can_retry(tmp_path):
 s=ProductService(tmp_path/'db');calls={'n':0}
 def processor(data,mime):
  calls['n']+=1
  if calls['n']==1:raise RuntimeError('ocr')
  return 'r2'
 inbox=InboxService(s,processor);result=inbox.receive('t','a@b.co','One',[{'filename':'r.png','content_type':'image/png','content_base64':base64.b64encode(png()).decode()}]);att=result['attachments'][0]
 assert result['status']=='failed' and att['error_code']=='ocr_failed'
 retried=inbox.retry('t',result['email_id'],att['attachment_id']);assert retried['status']=='completed' and retried['attempt']==2

def test_us_008_detects_deterministic_conflict(tmp_path):
 s=ProductService(tmp_path/'db');a=Actor('t','admin');adv=AdvancedWorkspace(s);auto=AutomationService(s,adv);s.create_receipt(a,parsed(),'r.png')
 first=auto.create(a,'First',{'vendor_contains':'Coffee'},{'cost_center':'A'},10);p=auto.preview(a,first['rule_id'],1);auto.activate(a,first['rule_id'],1,p['preview_token'])
 second=auto.create(a,'Second',{'vendor_contains':'Coffee'},{'cost_center':'B'},20);preview=auto.preview(a,second['rule_id'],1)
 assert preview['conflicts'][0]['field']=='cost_center' and preview['conflicts'][0]['winner_rule_id']==first['rule_id']

def test_us_009_rollback_is_atomic_under_injected_failure(tmp_path):
 s=ProductService(tmp_path/'db');a=Actor('t','admin');adv=AdvancedWorkspace(s);auto=AutomationService(s,adv);ids=[s.create_receipt(a,parsed(),f'{i}.png')['receipt_id'] for i in range(2)]
 rule=auto.create(a,'Tag',{}, {'tags':['x']},10);p=auto.preview(a,rule['rule_id'],1);auto.activate(a,rule['rule_id'],1,p['preview_token']);run=auto.run(a,rule['rule_id'],1,ids);versions=[s.get_receipt(a,x)['version'] for x in ids]
 with pytest.raises(sqlite3.OperationalError):auto.rollback(a,run['run_id'],ids,fail_after=1)
 assert [s.get_receipt(a,x)['version'] for x in ids]==versions

def test_security_cors_allowlist_and_csv_formula():
    from app.api import app
    from app.integrations import AccountingProfile, CsvAccountingConnector
    c=TestClient(app);ok=c.get('/health',headers={'Origin':'http://localhost:3000'});bad=c.get('/health',headers={'Origin':'https://evil.example'})
    assert ok.headers['access-control-allow-origin']=='http://localhost:3000' and 'access-control-allow-origin' not in bad.headers
    # BUG-007: the Playwright E2E stack serves the frontend on port 3010 —
    # it must be a permitted origin so the dashboard loads after sign-in.
    e2e=c.get('/health',headers={'Origin':'http://localhost:3010'})
    assert e2e.headers['access-control-allow-origin']=='http://localhost:3010'
    e2e_ip=c.get('/health',headers={'Origin':'http://127.0.0.1:3010'})
    assert e2e_ip.headers['access-control-allow-origin']=='http://127.0.0.1:3010'
    csv=CsvAccountingConnector(AccountingProfile(('vendor',))).export([{'vendor':'=cmd'}]);assert "'=cmd" in csv
