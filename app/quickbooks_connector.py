"""Minimal fixed-host QuickBooks Online API adapter."""
from typing import Any

import httpx


class QuickBooksConnector:
 def __init__(self,realm_id:str,token:str,client:httpx.Client|None=None,environment:str='sandbox'):
  self.realm_id,self.token=realm_id,token;self.client=client or httpx.Client(timeout=20);self.base='https://sandbox-quickbooks.api.intuit.com' if environment=='sandbox' else 'https://quickbooks.api.intuit.com'
 def _headers(self):return {'Authorization':f'Bearer {self.token}','Accept':'application/json'}
 def company(self,token:str|None=None):return self.client.get(f'{self.base}/v3/company/{self.realm_id}/companyinfo/{self.realm_id}',headers=self._headers()).raise_for_status().json()['CompanyInfo']
 def references(self,kind:str):
  entity={'accounts':'Account','tax_codes':'TaxCode','vendors':'Vendor'}[kind];r=self.client.get(f'{self.base}/v3/company/{self.realm_id}/query',params={'query':f'select * from {entity}'},headers=self._headers());r.raise_for_status();return r.json().get('QueryResponse',{}).get(entity,[])
 def create_purchase(self,payload:dict[str,Any],dedupe_key:str):
  body={**payload,'PrivateNote':f'ReceiptLens:{dedupe_key}'};r=self.client.post(f'{self.base}/v3/company/{self.realm_id}/purchase',json=body,headers=self._headers());r.raise_for_status();return r.json()['Purchase']
 def get_purchase(self,provider_id:str):
  r=self.client.get(f'{self.base}/v3/company/{self.realm_id}/purchase/{provider_id}',headers=self._headers())
  if r.status_code==404:raise KeyError(provider_id)
  r.raise_for_status();return r.json()['Purchase']
