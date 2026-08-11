"""Tenant-scoped QuickBooks OAuth state, credentials, health and mappings."""
from __future__ import annotations
import hashlib,json,secrets,uuid
from datetime import UTC,datetime,timedelta
from typing import Any
from urllib.parse import urlencode
class ConnectionService:
 def __init__(self,service:Any,credentials:Any):
  self.db,self.credentials=service._db,credentials
  with self.db:
   self.db.executescript('''CREATE TABLE IF NOT EXISTS oauth_states(state_hash TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,return_path TEXT NOT NULL,expires_at TEXT NOT NULL,used_at TEXT);CREATE TABLE IF NOT EXISTS provider_connections(connection_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,provider TEXT NOT NULL,provider_company_id TEXT NOT NULL,provider_company_name TEXT NOT NULL,health TEXT NOT NULL,reauthorization_required INTEGER NOT NULL,created_at TEXT NOT NULL,last_tested_at TEXT);CREATE TABLE IF NOT EXISTS provider_credentials(connection_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,token_ciphertext TEXT NOT NULL,expires_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS connection_mapping_versions(mapping_id TEXT PRIMARY KEY,connection_id TEXT NOT NULL,tenant_id TEXT NOT NULL,version INTEGER NOT NULL,payload_json TEXT NOT NULL,snapshot_hash TEXT NOT NULL,valid INTEGER NOT NULL,created_at TEXT NOT NULL,UNIQUE(connection_id,version));''')
 @staticmethod
 def now():return datetime.now(UTC)
 def start_oauth(self,actor,return_path):
  if actor.role!='admin':raise PermissionError
  if return_path!='/integrations':raise ValueError('return path not allowed')
  state=secrets.token_urlsafe(32);h=hashlib.sha256(state.encode()).hexdigest();exp=self.now()+timedelta(minutes=10)
  with self.db:self.db.execute('INSERT INTO oauth_states VALUES(?,?,?,?,NULL)',(h,actor.tenant_id,return_path,exp.isoformat()))
  q=urlencode({'client_id':'configured','response_type':'code','scope':'com.intuit.quickbooks.accounting','redirect_uri':'/product/connections/quickbooks/oauth/callback','state':state,'code_challenge_method':'S256'})
  return {'authorization_url':'https://appcenter.intuit.com/connect/oauth2?'+q,'state':state,'state_expires_at':exp.isoformat()}
 def complete_oauth(self,actor,state,code,realm,tokens):
  h=hashlib.sha256(state.encode()).hexdigest();row=self.db.execute('SELECT * FROM oauth_states WHERE state_hash=? AND tenant_id=?',(h,actor.tenant_id)).fetchone()
  if not row or row['used_at'] or datetime.fromisoformat(row['expires_at'])<self.now():raise ValueError('oauth_state_invalid')
  cid=str(uuid.uuid4());now=self.now();exp=now+timedelta(seconds=int(tokens.get('expires_in',3600)))
  with self.db:
   self.db.execute('UPDATE oauth_states SET used_at=? WHERE state_hash=?',(now.isoformat(),h))
   self.db.execute('INSERT INTO provider_connections VALUES(?,?,?,?,?,"healthy",0,?,NULL)',(cid,actor.tenant_id,'quickbooks_online',realm,'QuickBooks Sandbox',now.isoformat()))
   self.db.execute('INSERT INTO provider_credentials VALUES(?,?,?,?,?)',(cid,actor.tenant_id,self.credentials.encrypt(tokens),exp.isoformat(),now.isoformat()))
  return self.get(actor,cid)
 def get(self,actor,cid):
  r=self.db.execute('SELECT * FROM provider_connections WHERE tenant_id=? AND connection_id=?',(actor.tenant_id,cid)).fetchone()
  if not r:raise KeyError(cid)
  d=dict(r);d['reauthorization_required']=bool(d['reauthorization_required']);return d
 def rotate_tokens(self,actor,cid,tokens):
  self.get(actor,cid);now=self.now();exp=now+timedelta(seconds=int(tokens.get('expires_in',3600)))
  with self.db:self.db.execute('UPDATE provider_credentials SET token_ciphertext=?,expires_at=?,updated_at=? WHERE tenant_id=? AND connection_id=?',(self.credentials.encrypt(tokens),exp.isoformat(),now.isoformat(),actor.tenant_id,cid))
 def test_connection(self,actor,cid,provider):
  self.get(actor,cid);r=self.db.execute('SELECT token_ciphertext FROM provider_credentials WHERE connection_id=? AND tenant_id=?',(cid,actor.tenant_id)).fetchone();t=self.credentials.decrypt(r[0]);company=provider.company(t['access_token']);now=self.now().isoformat()
  with self.db:self.db.execute('UPDATE provider_connections SET health="healthy",reauthorization_required=0,last_tested_at=?,provider_company_name=? WHERE connection_id=?',(now,company['name'],cid))
  return {'health':'healthy','company':company,'tested_at':now}
 def mark_reauthorization(self,actor,cid):
  self.get(actor,cid)
  with self.db:self.db.execute('UPDATE provider_connections SET health="reauthorization_required",reauthorization_required=1 WHERE connection_id=?',(cid,))
 def validate_mapping(self,mapping,provider):
  ref=mapping.get('expense_account_ref');refs=provider.references('accounts')
  if not ref:raise ValueError('expense_account_ref is required')
  if ref not in {x['id'] for x in refs if x.get('active')}:raise ValueError('mapping_reference_inactive')
  snap=hashlib.sha256(json.dumps(refs,sort_keys=True).encode()).hexdigest();return {'valid':True,'mapping':mapping,'snapshot_hash':snap}
 def save_mapping(self,actor,cid,mapping,snapshot_hash):
  self.get(actor,cid);v=self.db.execute('SELECT COALESCE(MAX(version),0)+1 FROM connection_mapping_versions WHERE connection_id=?',(cid,)).fetchone()[0];mid=str(uuid.uuid4())
  with self.db:self.db.execute('INSERT INTO connection_mapping_versions VALUES(?,?,?,?,?,?,1,?)',(mid,cid,actor.tenant_id,v,json.dumps(mapping,sort_keys=True),snapshot_hash,self.now().isoformat()))
  return {'mapping_id':mid,'version':v,'valid':True,'mapping':mapping,'snapshot_hash':snapshot_hash}
