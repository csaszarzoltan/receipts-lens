import base64
import os

from fastapi.testclient import TestClient

os.environ['RECEIPTLENS_CREDENTIAL_KEY']=base64.urlsafe_b64encode(b'k'*32).decode()
from app.api import app

H={'X-Tenant-ID':'completion','X-Role':'admin'}

def test_us_010_oauth_start_is_real_and_tenant_safe():
 r=TestClient(app).post('/product/connections/quickbooks/oauth/start',json={'return_path':'/integrations'},headers=H)
 assert r.status_code==201 and 'appcenter.intuit.com' in r.json()['authorization_url'] and 'state' not in r.json()

def test_us_012_mapping_validation_is_field_specific():
 r=TestClient(app).post('/product/provider-mappings/validate',json={'expense_account_ref':''},headers=H)
 assert r.status_code==422

def test_us_016_projection_missing_rate_is_observable():
 r=TestClient(app).post('/product/receipts/missing/accounting-projection/refresh',json={'reporting_currency':'CHF'},headers=H)
 assert r.status_code==404

def test_us_018_payload_preview_is_role_limited():
 r=TestClient(app).get('/product/receipts/missing/provider-preview?receipt_version=1&mapping_version=1',headers={'X-Tenant-ID':'completion','X-Role':'integrator'})
 assert r.status_code==403
