"""FastAPI adapter for FEAT-039."""
from __future__ import annotations
import uuid
from fastapi import APIRouter,Header,HTTPException,Response
from fastapi.responses import JSONResponse
from app.missing_receipt_models import CreateRequest,CommandRequest,DomainError
from app.missing_receipt_service import service
router=APIRouter(prefix="/api/v2/missing-receipts",tags=["FEAT-039"])

def context(authorization:str|None=Header(None,alias="Authorization"),x_tenant_id:str|None=Header(None,alias="X-Tenant-ID"),x_role:str|None=Header(None,alias="X-Role")):
    if not authorization or not x_tenant_id: raise HTTPException(401,"Authentication required")
    if x_role not in {"admin","owner","member","accountant"}: raise HTTPException(403,"Role denied")
    return x_tenant_id

def key(value:str|None):
    if not value or len(value)<16: raise HTTPException(422,"Idempotency-Key must be at least 16 characters")
    return value

def problem(exc:DomainError): return JSONResponse(status_code=exc.status_code,media_type="application/problem+json",content={"code":exc.code,"message":exc.message,"retryable":False,"correlation_id":uuid.uuid4().hex})

@router.get("")
def list_items(authorization:str|None=Header(None,alias="Authorization"),x_tenant_id:str|None=Header(None,alias="X-Tenant-ID"),x_role:str|None=Header(None,alias="X-Role")):
    tenant=context(authorization,x_tenant_id,x_role); return {"items":[x.model_dump(mode="json") for x in service.list(tenant)]}
@router.post("",status_code=201)
def create_item(request:CreateRequest,authorization:str|None=Header(None,alias="Authorization"),x_tenant_id:str|None=Header(None,alias="X-Tenant-ID"),x_role:str|None=Header(None,alias="X-Role"),idempotency_key:str|None=Header(None,alias="Idempotency-Key")):
    try: return service.create(context(authorization,x_tenant_id,x_role),key(idempotency_key),request)
    except DomainError as exc: return problem(exc)
@router.get("/{item_id}")
def get_item(item_id:str,authorization:str|None=Header(None,alias="Authorization"),x_tenant_id:str|None=Header(None,alias="X-Tenant-ID"),x_role:str|None=Header(None,alias="X-Role")):
    try: return service.get(context(authorization,x_tenant_id,x_role),item_id)
    except DomainError as exc: return problem(exc)
@router.patch("/{item_id}")
def patch_item(item_id:str,request:CommandRequest,authorization:str|None=Header(None,alias="Authorization"),x_tenant_id:str|None=Header(None,alias="X-Tenant-ID"),x_role:str|None=Header(None,alias="X-Role"),idempotency_key:str|None=Header(None,alias="Idempotency-Key")):
    try: return service.command(context(authorization,x_tenant_id,x_role),item_id,key(idempotency_key),request)
    except DomainError as exc: return problem(exc)
@router.post("/{item_id}/confirm")
def confirm(item_id:str,request:CommandRequest,authorization:str|None=Header(None,alias="Authorization"),x_tenant_id:str|None=Header(None,alias="X-Tenant-ID"),x_role:str|None=Header(None,alias="X-Role"),idempotency_key:str|None=Header(None,alias="Idempotency-Key")):
    request.action="confirm"; return patch_item(item_id,request,authorization,x_tenant_id,x_role,idempotency_key)
