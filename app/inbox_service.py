"""Durable, tenant-scoped inbound email attachment processing."""
from __future__ import annotations

import base64
import hashlib
import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

MAX_ATTACHMENT_BYTES = 20_000_000
MAX_ATTACHMENTS = 20
SIGNATURES = {
 "image/jpeg": (b"\xff\xd8\xff",), "image/png": (b"\x89PNG\r\n\x1a\n",),
 "image/gif": (b"GIF87a", b"GIF89a"), "image/bmp": (b"BM",),
 "image/tiff": (b"II*\x00", b"MM\x00*"), "application/pdf": (b"%PDF-",),
}
def safe_filename(value: str) -> str:
 name=re.sub(r"[^A-Za-z0-9._ -]+","_",value.replace("\\","/").split("/")[-1]).strip(" .")
 return (name or "attachment")[:180]
def detect_type(content: bytes) -> str | None:
 if len(content)>=12 and content[:4]==b"RIFF" and content[8:12]==b"WEBP": return "image/webp"
 for mime,sigs in SIGNATURES.items():
  if any(content.startswith(sig) for sig in sigs): return mime
 return None
class InboxService:
 def __init__(self, service: Any, processor: Callable[[bytes,str],str|None]|None=None) -> None:
  self.service,self.db,self.processor=service,service._db,processor
  with self.db:self.db.executescript("""
  CREATE TABLE IF NOT EXISTS inbound_emails(
   email_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,sender TEXT NOT NULL,subject TEXT NOT NULL,
   attachments TEXT NOT NULL,status TEXT NOT NULL,error TEXT,created_at TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS inbound_email_attachments(
   attachment_id TEXT PRIMARY KEY,email_id TEXT NOT NULL,tenant_id TEXT NOT NULL,filename TEXT NOT NULL,
   declared_type TEXT NOT NULL,detected_type TEXT,size_bytes INTEGER NOT NULL,sha256 TEXT NOT NULL,
   content BLOB,status TEXT NOT NULL,attempt INTEGER NOT NULL,receipt_id TEXT,error_code TEXT,
   created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
  """)
 @staticmethod
 def now()->str:return datetime.now(UTC).isoformat()
 def receive(self,tenant:str,sender:str,subject:str,attachments:list[dict[str,Any]])->dict[str,Any]:
  if len(attachments)>MAX_ATTACHMENTS:raise ValueError("maximum 20 attachments")
  eid=str(uuid.uuid4()); now=self.now()
  with self.db:
   self.db.execute("INSERT INTO inbound_emails VALUES(?,?,?,?,?,?,NULL,?)",(eid,tenant,sender,subject,"[]","processing",now))
   for raw in attachments:self._insert(tenant,eid,raw,now)
   self._refresh(eid,tenant)
  return self.get(tenant,eid)
 def _insert(self,tenant:str,eid:str,raw:dict[str,Any],now:str)->None:
  aid=str(uuid.uuid4()); name=safe_filename(str(raw.get("filename") or "attachment")); declared=str(raw.get("content_type") or "application/octet-stream")
  encoded=raw.get("content_base64"); content=b""
  try: content=base64.b64decode(encoded,validate=True) if isinstance(encoded,str) and encoded else b""
  except Exception: pass
  detected=detect_type(content) if content else None; status="queued"; error=None
  if len(content)>MAX_ATTACHMENT_BYTES:status,error="quarantined","attachment_too_large"
  elif not content:status,error="failed","content_missing"
  elif detected not in SIGNATURES and detected!="image/webp":status,error="quarantined","unsupported_content"
  elif declared!=detected:status,error="quarantined","mime_mismatch"
  elif detected=="application/pdf":status,error="failed","pdf_processing_unavailable"
  else:
   try:
    receipt=self.processor(content,detected) if self.processor else None; status="completed"; error=None
   except Exception:receipt=None;status,error="failed","ocr_failed"
  self.db.execute("INSERT INTO inbound_email_attachments VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
   (aid,eid,tenant,name,declared,detected,len(content),hashlib.sha256(content).hexdigest(),content,status,1,locals().get('receipt'),error,now,now))
 def _refresh(self,eid:str,tenant:str)->None:
  states=[r[0] for r in self.db.execute("SELECT status FROM inbound_email_attachments WHERE email_id=? AND tenant_id=?",(eid,tenant))]
  if not states:status="failed"
  elif all(x=="completed" for x in states):status="completed"
  elif any(x=="completed" for x in states):status="partial"
  elif all(x=="quarantined" for x in states):status="quarantined"
  elif any(x in {"queued","processing"} for x in states):status="processing"
  else:status="failed"
  self.db.execute("UPDATE inbound_emails SET status=? WHERE email_id=? AND tenant_id=?",(status,eid,tenant))
 def get(self,tenant:str,eid:str)->dict[str,Any]:
  e=self.db.execute("SELECT * FROM inbound_emails WHERE tenant_id=? AND email_id=?",(tenant,eid)).fetchone()
  if not e:raise KeyError(eid)
  rows=self.db.execute("SELECT attachment_id,filename,declared_type,detected_type,size_bytes,sha256,status,attempt,receipt_id,error_code,created_at,updated_at FROM inbound_email_attachments WHERE tenant_id=? AND email_id=? ORDER BY created_at",(tenant,eid)).fetchall()
  return {"email_id":eid,"sender":e["sender"],"subject":e["subject"],"status":e["status"],"created_at":e["created_at"],"attachments":[dict(r) for r in rows]}
 def list(self,tenant:str)->list[dict[str,Any]]:
  return [self.get(tenant,r[0]) for r in self.db.execute("SELECT email_id FROM inbound_emails WHERE tenant_id=? ORDER BY created_at DESC",(tenant,))]
 def retry(self,tenant:str,eid:str,aid:str)->dict[str,Any]:
  row=self.db.execute("SELECT * FROM inbound_email_attachments WHERE tenant_id=? AND email_id=? AND attachment_id=?",(tenant,eid,aid)).fetchone()
  if not row:raise KeyError(aid)
  if row["status"]=="quarantined":raise ValueError("quarantined attachments cannot be retried")
  status,error,receipt="completed",None,None
  try: receipt=self.processor(row["content"],row["detected_type"]) if self.processor else None
  except Exception:status,error="failed","ocr_failed"
  with self.db:
   self.db.execute("UPDATE inbound_email_attachments SET status=?,attempt=attempt+1,receipt_id=?,error_code=?,updated_at=? WHERE attachment_id=?",(status,receipt,error,self.now(),aid));self._refresh(eid,tenant)
  return next(x for x in self.get(tenant,eid)["attachments"] if x["attachment_id"]==aid)
