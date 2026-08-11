"""Authenticated encryption for provider credentials."""
from __future__ import annotations
import base64,json,os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
class CredentialStore:
 def __init__(self,key:bytes|None=None):
  key=key or self.key_from_env();
  if len(key)!=32: raise ValueError('credential key must be 32 bytes')
  self.key=key
 @staticmethod
 def key_from_env()->bytes:
  raw=os.getenv('RECEIPTLENS_CREDENTIAL_KEY','')
  try:return base64.urlsafe_b64decode(raw.encode())
  except Exception:return b''
 def encrypt(self,value:dict)->str:
  nonce=os.urandom(12);data=json.dumps(value,sort_keys=True,separators=(',',':')).encode();return base64.urlsafe_b64encode(nonce+AESGCM(self.key).encrypt(nonce,data,b'receiptlens:qbo:v1')).decode()
 def decrypt(self,value:str)->dict:
  raw=base64.urlsafe_b64decode(value);return json.loads(AESGCM(self.key).decrypt(raw[:12],raw[12:],b'receiptlens:qbo:v1'))
