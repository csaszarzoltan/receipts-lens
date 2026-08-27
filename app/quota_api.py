import os
from fastapi import APIRouter,Depends,HTTPException
from app.product_api import Actor,actor
from app.quota import quota_store
from app.subscriptions_api import is_pro
router=APIRouter()
@router.get("/api/v1/quota")
def quota(current:Actor=Depends(actor)):return quota_store.get_quota(current.tenant_id,is_pro(current.tenant_id))
@router.post("/api/v1/quota/reset")
def reset(current:Actor=Depends(actor)):
 if os.getenv("RECEIPTLENS_ENV")=="production":raise HTTPException(404,"Not found")
 quota_store.reset(current.tenant_id);return quota_store.get_quota(current.tenant_id,is_pro(current.tenant_id))
