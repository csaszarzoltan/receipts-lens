"""HTTP and HTML adapters for the six ReceiptLens product features."""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.ocr import parse_receipt_with_confidence
from app.product_service import Actor, ProductConflict, ProductService

router = APIRouter()
service = ProductService(os.getenv("RECEIPTLENS_PRODUCT_DB", ":memory:"))


def actor(x_tenant_id: str = Header(default="demo"), x_role: str = Header(default="admin")) -> Actor:
    if not x_tenant_id.strip(): raise HTTPException(401, "Tenant identity is required")
    if x_role not in {"admin", "reviewer", "integrator"}: raise HTTPException(403, "Unknown role")
    return Actor(x_tenant_id, x_role)


class CorrectionRequest(BaseModel):
    changes: dict[str, Any]
    action: str = Field(pattern="^(save|complete)$")

class MemberRequest(BaseModel):
    email: str = Field(min_length=3)
    role: str

class ApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class ConnectionRequest(BaseModel):
    name: str = Field(min_length=1)
    provider: str
    mapping: dict[str, str]

class ExportRequest(BaseModel):
    connection_id: str
    receipt_ids: list[str]


@router.get("/workspace", response_class=HTMLResponse, include_in_schema=False)
def workspace() -> str:
    return """<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>ReceiptLens Workspace</title><style>body{font-family:system-ui;max-width:900px;margin:40px auto;padding:0 20px;background:#f4f7fb;color:#182033}.card{background:white;padding:28px;border-radius:16px}button{padding:12px 18px;background:#2563eb;color:white;border:0;border-radius:9px}pre{white-space:pre-wrap;background:#111827;color:white;padding:16px}</style></head><body><div class='card'><h1>Upload receipt</h1><p>Choose a receipt image to extract fields and confidence scores.</p><input id='file' type='file' accept='image/*'><button id='upload'>Process receipt</button><p id='status' role='status'></p><pre id='result'></pre></div><script>document.getElementById('upload').onclick=async()=>{const f=document.getElementById('file').files[0];if(!f){document.getElementById('status').textContent='Choose a file first.';return}const form=new FormData();form.append('file',f);document.getElementById('status').textContent='Processing…';const r=await fetch('/product/receipts/upload',{method:'POST',body:form,headers:{'X-Tenant-ID':'demo','X-Role':'admin'}});const b=await r.json();document.getElementById('status').textContent=r.ok?'Completed':'Processing failed';document.getElementById('result').textContent=JSON.stringify(b,null,2)}</script></body></html>"""


@router.post("/product/receipts/upload", status_code=201)
async def upload_receipt(file: UploadFile = File(...), current: Actor = Depends(actor)) -> dict[str, Any]:
    if file.content_type and not file.content_type.startswith("image/"): raise HTTPException(415, "An image file is required")
    data=await file.read()
    if not data: raise HTTPException(422, "The uploaded file is empty")
    try: parsed=parse_receipt_with_confidence(data)
    except Exception as exc: raise HTTPException(422, "Receipt processing failed") from exc
    return service.create_receipt(current,parsed,file.filename or "receipt")

@router.get("/product/jobs")
def jobs(current: Actor = Depends(actor)) -> dict[str, Any]: return {"items":service.list_jobs(current)}

@router.post("/product/jobs/{job_id}/retry")
def retry_job(job_id: str, current: Actor = Depends(actor)) -> dict[str, Any]:
    try:return service.retry(current,job_id)
    except KeyError:raise HTTPException(404,"Job not found")

@router.post("/product/jobs/{job_id}/cancel")
def cancel_job(job_id: str, current: Actor = Depends(actor)) -> dict[str, Any]:
    try:return service.cancel(current,job_id)
    except KeyError:raise HTTPException(404,"Job not found")
    except ProductConflict as exc:raise HTTPException(409,str(exc))

@router.get("/product/review-items")
def reviews(current: Actor = Depends(actor)) -> dict[str, Any]: return {"items":service.list_reviews(current)}

@router.patch("/product/review-items/{receipt_id}")
def correct(receipt_id: str, body: CorrectionRequest, if_match: int = Header(alias="If-Match"), current: Actor = Depends(actor)) -> dict[str, Any]:
    if current.role not in {"admin","reviewer"}: raise HTTPException(403,"Reviewer role required")
    try:return service.correct(current,receipt_id,body.changes,if_match,body.action=="complete")
    except KeyError:raise HTTPException(404,"Review item not found")
    except ProductConflict as exc:raise HTTPException(409,str(exc))
    except ValueError as exc:raise HTTPException(422,str(exc))

@router.post("/product/members",status_code=201)
def add_member(body:MemberRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return service.add_member(current,body.email,body.role)
    except PermissionError:raise HTTPException(403,"Admin role required")
    except ValueError as exc:raise HTTPException(422,str(exc))

@router.post("/product/api-keys",status_code=201)
def create_key(body:ApiKeyRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return service.create_api_key(current,body.name)
    except PermissionError:raise HTTPException(403,"Admin role required")

@router.post("/product/connections",status_code=201)
def create_connection(body:ConnectionRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return service.create_connection(current,body.name,body.provider,body.mapping)
    except ValueError as exc:raise HTTPException(422,str(exc))

@router.post("/product/connections/{connection_id}/test")
def test_connection(connection_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try:return service.test_connection(current,connection_id)
    except KeyError:raise HTTPException(404,"Connection not found")

@router.post("/product/exports",status_code=201)
def create_export(body:ExportRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return service.export(current,body.connection_id,body.receipt_ids)
    except KeyError:raise HTTPException(404,"Connection not found")

@router.get("/product/dashboard")
def dashboard(current:Actor=Depends(actor))->dict[str,Any]: return service.dashboard(current)
