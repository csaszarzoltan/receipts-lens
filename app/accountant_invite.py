"""Hashed, expiring, tenant-safe accountant invites."""
import hashlib,secrets,threading
from datetime import UTC,datetime,timedelta
class AccountantInviteStore:
 def __init__(self,now=None):self.now=now or (lambda:datetime.now(UTC));self.items={};self.lock=threading.Lock()
 def create_invite(self,tenant_id,days_valid=30):
  if not 1<=days_valid<=90:raise ValueError("days_valid must be 1..90")
  token=secrets.token_urlsafe(32);expires=self.now()+timedelta(days=days_valid)
  with self.lock:self.items[hashlib.sha256(token.encode()).hexdigest()]={"tenant_id":tenant_id,"expires_at":expires,"revoked":False}
  return {"token":token,"expires_at":expires.isoformat()}
 def resolve_invite(self,token):
  x=self.items.get(hashlib.sha256(token.encode()).hexdigest())
  return None if not x or x["revoked"] or x["expires_at"]<=self.now() else {"tenant_id":x["tenant_id"],"expires_at":x["expires_at"].isoformat()}
 def revoke_invite(self,token,tenant_id):
  x=self.items.get(hashlib.sha256(token.encode()).hexdigest())
  if not x or x["tenant_id"]!=tenant_id:return False
  x["revoked"]=True;return True
invite_store=AccountantInviteStore()
