import base64
import os

from fastapi.testclient import TestClient

os.environ['RECEIPTLENS_CREDENTIAL_KEY']=base64.urlsafe_b64encode(b'q'*32).decode()
from app.api import app

H={'X-Tenant-ID':'qbo-complete','X-Role':'admin'}

def test_us_010_start_rejects_open_redirect():
 r=TestClient(app).post('/product/connections/quickbooks/oauth/start',json={'return_path':'https://evil.example'},headers=H)
 assert r.status_code==422

def test_us_011_connection_list_is_tenant_scoped():
 c=TestClient(app)
 r=c.get('/product/provider-connections',headers=H)
 assert r.status_code==200 and r.json()=={'items':[]}

def test_us_012_mapping_save_and_current_are_versioned():
 c=TestClient(app)
 # a provider connection is created through the tested service callback because live Intuit is not called in contract tests
 from app.product_api import _connections, service
 actor=type('A',(),{'tenant_id':'qbo-complete','role':'admin'})()
 cs=_connections(); start=cs.start_oauth(actor,'/integrations')
 conn=cs.complete_oauth(actor,start['state'],'code','realm-test',{'access_token':'a','refresh_token':'r','expires_in':3600})
 body={'expense_account_ref':'acct-1','tax_strategy':'exclusive','snapshot_hash':'snap'}
 saved=c.post(f"/product/connections/{conn['connection_id']}/mappings",json=body,headers=H)
 assert saved.status_code==201 and saved.json()['version']==1
 current=c.get(f"/product/connections/{conn['connection_id']}/mappings/current",headers=H)
 assert current.status_code==200 and current.json()['version']==1

def test_us_011_disconnect_removes_active_credentials_but_keeps_connection():
 c=TestClient(app)
 from app.product_api import _connections, service
 actor=type('A',(),{'tenant_id':'disconnect-tenant','role':'admin'})()
 cs=_connections(); st=cs.start_oauth(actor,'/integrations'); conn=cs.complete_oauth(actor,st['state'],'c','realm-d',{'access_token':'a','refresh_token':'r'})
 r=c.post(f"/product/connections/{conn['connection_id']}/disconnect",headers={'X-Tenant-ID':'disconnect-tenant','X-Role':'admin'})
 assert r.status_code==200 and r.json()['health']=='disconnected'
 assert service._db.execute('SELECT 1 FROM provider_credentials WHERE connection_id=?',(conn['connection_id'],)).fetchone() is None
