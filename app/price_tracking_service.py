"""Tenant-isolated, idempotent service for FEAT-041."""
from __future__ import annotations
from datetime import UTC,datetime
import hashlib,json,threading,uuid
from app.price_tracking_models import TrackedProduct,CreateRequest,CommandRequest,Status,NotFoundError,StaleRevisionError,IdempotencyConflictError

class TrackedProductService:
    def __init__(self): self._items={}; self._keys={}; self._lock=threading.RLock()
    def list(self,tenant_id:str): return [v for (t,_),v in self._items.items() if t==tenant_id]
    def get(self,tenant_id:str,item_id:str):
        value=self._items.get((tenant_id,item_id))
        if value is None: raise NotFoundError()
        return value
    def create(self,tenant_id:str,key:str,request:CreateRequest):
        digest=hashlib.sha256(request.model_dump_json().encode()).hexdigest(); token=(tenant_id,key)
        with self._lock:
            prior=self._keys.get(token)
            if prior:
                if prior[0]!=digest: raise IdempotencyConflictError()
                return self.get(tenant_id,prior[1])
            item=TrackedProduct(id=uuid.uuid4().hex,tenant_id=tenant_id,status=Status.CANDIDATE,revision=0,client_reference=request.client_reference,data=request.payload,evidence={"source":"FEAT-041"})
            self._items[(tenant_id,item.id)]=item; self._keys[token]=(digest,item.id); return item
    def command(self,tenant_id:str,item_id:str,key:str,request:CommandRequest):
        digest=hashlib.sha256(request.model_dump_json().encode()).hexdigest(); token=(tenant_id,key)
        with self._lock:
            prior=self._keys.get(token)
            if prior:
                if prior[0]!=digest: raise IdempotencyConflictError()
                return self.get(tenant_id,prior[1])
            item=self.get(tenant_id,item_id)
            if item.revision!=request.expected_revision: raise StaleRevisionError()
            target={"confirm":"PAUSED","reject":"ARCHIVED","resolve":"PAUSED","reopen":"CANDIDATE"}.get(request.action,item.status.value)
            updated=item.model_copy(update={"status":Status(target),"revision":item.revision+1,"updated_at":datetime.now(UTC),"data":{**item.data,**request.payload,"reason":request.reason}})
            self._items[(tenant_id,item_id)]=updated; self._keys[token]=(digest,item_id); return updated
service=TrackedProductService()
