"""HTTP and HTML adapters for the six ReceiptLens product features."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, Field

from app.accounting_workspace import AccountingWorkspace
from app.advanced_workspace import AdvancedWorkspace, extract_ocr_boxes
from app.ocr import parse_receipt_with_confidence
from app.product_service import Actor, ProductConflict, ProductService

router = APIRouter()
service = ProductService(os.getenv("RECEIPTLENS_PRODUCT_DB", ":memory:"))
advanced = AdvancedWorkspace(service)


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
def workspace() -> HTMLResponse:
    html = (Path(__file__).parent / "static" / "workspace.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@router.get("/assets/{asset_name}", include_in_schema=False)
def workspace_asset(asset_name: str) -> FileResponse:
    allowed = {"workspace.css", "workspace.js", "manifest.webmanifest", "service-worker.js"}
    if asset_name not in allowed:
        raise HTTPException(404, "Asset not found")
    return FileResponse(Path(__file__).parent / "static" / asset_name)


@router.post("/product/receipts/upload", status_code=201)
async def upload_receipt(file: UploadFile = File(...), current: Actor = Depends(actor)) -> dict[str, Any]:
    if file.content_type and not file.content_type.startswith("image/"): raise HTTPException(415, "An image file is required")
    data=await file.read()
    if not data: raise HTTPException(422, "The uploaded file is empty")
    try: parsed=parse_receipt_with_confidence(data)
    except Exception as exc: raise HTTPException(422, "Receipt processing failed") from exc
    result = service.create_receipt(current,parsed,file.filename or "receipt")
    advanced.store_asset(current.tenant_id, result["receipt_id"], data,
                         file.content_type or "application/octet-stream",
                         file.filename or "receipt", extract_ocr_boxes(data))
    advanced.record_history(current, result["receipt_id"], "receipt.created", None,
                            result["receipt"])
    applied = advanced.apply_rules(current, result["receipt_id"], result["receipt"])
    result["applied_rules"] = applied
    if result["status"] == "needs_review":
        advanced.notify(current.tenant_id, "review", "Nyugta ellenőrzést igényel",
                        file.filename or "A feltöltött nyugta", result["receipt_id"])
    return result

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
    try:
        row = service._db.execute("SELECT payload FROM receipts WHERE tenant_id=? AND receipt_id=?",
                                  (current.tenant_id, receipt_id)).fetchone()
        before = json.loads(row["payload"]) if row else None
        result = service.correct(current,receipt_id,body.changes,if_match,body.action=="complete")
        advanced.record_history(current, receipt_id, "receipt.corrected", before, result["receipt"])
        return result
    except KeyError:raise HTTPException(404,"Review item not found")
    except ProductConflict as exc:raise HTTPException(409,str(exc))
    except ValueError as exc:raise HTTPException(422,str(exc))

@router.get("/product/members")
def list_members(current:Actor=Depends(actor))->dict[str,Any]:
    return {"items": service.list_members(current)}

@router.post("/product/members",status_code=201)
def add_member(body:MemberRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return service.add_member(current,body.email,body.role)
    except PermissionError:raise HTTPException(403,"Admin role required")
    except ValueError as exc:raise HTTPException(422,str(exc))

@router.post("/product/api-keys",status_code=201)
def create_key(body:ApiKeyRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return service.create_api_key(current,body.name)
    except PermissionError:raise HTTPException(403,"Admin role required")

@router.get("/product/connections")
def list_connections(current:Actor=Depends(actor))->dict[str,Any]:
    return {"items": service.list_connections(current)}

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

class MetadataRequest(BaseModel):
    tags: list[str] = []
    project: str | None = None
    cost_center: str | None = None

class WorkspaceUpdateRequest(BaseModel):
    """One atomic save for the high-frequency receipt review workspace."""
    fields: dict[str, Any] = {}
    line_items: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] | None = None
    action: str = Field(default="save", pattern="^(save|complete)$")

class ApprovalPolicyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    threshold: float
    currency: str = Field(default="USD", min_length=3, max_length=3)

class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    note: str | None = Field(default=None, max_length=500)

class RetentionRequest(BaseModel):
    retention_days: int

@router.get("/product/receipts")
def search_receipts(query: str | None = None, status: str | None = None,
                    tag: str | None = None, min_total: float | None = None,
                    max_total: float | None = None, limit: int = 50, offset: int = 0,
                    readiness: str | None = None,
                    current: Actor = Depends(actor)) -> dict[str, Any]:
    try: return service.search_receipts(current,query,status,tag,min_total,max_total,limit,offset,readiness)
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.get("/product/work-queue")
def work_queue(limit: int = 100, current: Actor = Depends(actor)) -> dict[str, Any]:
    """Rank failures, review items and approvals into one daily work queue."""
    try:
        return service.work_queue(current, limit)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.patch("/product/receipts/{receipt_id}/workspace")
def update_receipt_workspace(
    receipt_id: str, body: WorkspaceUpdateRequest,
    if_match: int = Header(alias="If-Match"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    current: Actor = Depends(actor),
) -> dict[str, Any]:
    """Atomically save fields, line items and metadata for daily review work."""
    # The command is already protected by optimistic concurrency. The optional
    # idempotency header is accepted now so clients can adopt the stable contract.
    del idempotency_key
    try:
        result = service.update_receipt_workspace(
            current, receipt_id, if_match, body.fields, body.line_items,
            body.metadata, body.action == "complete",
        )
        advanced.record_history(current, receipt_id, "receipt.workspace.updated",
                                None, {"version": result["version"]})
        return result
    except PermissionError as exc:
        raise HTTPException(403, "Reviewer role required") from exc
    except KeyError as exc:
        raise HTTPException(404, "Receipt not found") from exc
    except ProductConflict as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.put("/product/receipts/{receipt_id}/metadata")
def update_metadata(receipt_id: str, body: MetadataRequest,
                    current: Actor = Depends(actor)) -> dict[str, Any]:
    try: return service.set_metadata(current,receipt_id,body.tags,body.project,body.cost_center)
    except KeyError: raise HTTPException(404,"Receipt not found")
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.post("/product/approval-policies",status_code=201)
def create_approval_policy(body: ApprovalPolicyRequest,
                           current: Actor = Depends(actor)) -> dict[str, Any]:
    try: return service.create_approval_policy(current,body.name,body.threshold,body.currency)
    except PermissionError: raise HTTPException(403,"Admin role required")
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.post("/product/receipts/{receipt_id}/approval")
def request_approval(receipt_id: str,current: Actor = Depends(actor)) -> dict[str, Any]:
    try: return service.request_approval(current,receipt_id)
    except KeyError: raise HTTPException(404,"Receipt not found")

@router.get("/product/approvals")
def list_approvals(status: str | None = None,current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": service.list_approvals(current,status)}

@router.post("/product/approvals/{approval_id}/decision")
def decide_approval(approval_id: str,body: ApprovalDecisionRequest,
                    current: Actor = Depends(actor)) -> dict[str, Any]:
    try: return service.decide_approval(current,approval_id,body.decision,body.note)
    except PermissionError: raise HTTPException(403,"Reviewer role required")
    except KeyError: raise HTTPException(404,"Approval not found")
    except ProductConflict as exc: raise HTTPException(409,str(exc)) from exc
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.put("/product/privacy/retention")
def set_retention(body: RetentionRequest,current: Actor = Depends(actor)) -> dict[str, Any]:
    try: return service.set_retention(current,body.retention_days)
    except PermissionError: raise HTTPException(403,"Admin role required")
    except ValueError as exc: raise HTTPException(422,str(exc)) from exc

@router.post("/product/privacy/purge")
def purge_expired(current: Actor = Depends(actor)) -> dict[str, Any]:
    try: return service.purge_expired(current)
    except PermissionError: raise HTTPException(403,"Admin role required")

@router.get("/product/privacy/export")
def portability_export(current: Actor = Depends(actor)) -> dict[str, Any]:
    return service.portability_export(current)


class SavedViewRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    filters: dict[str, Any]
    shared: bool = False
    pinned: bool = False

class NotificationUpdateRequest(BaseModel):
    read: bool | None = None
    archived: bool | None = None

class AutomationRuleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    conditions: dict[str, Any]
    actions: dict[str, Any]
    priority: int = 100

class DuplicateDecisionRequest(BaseModel):
    left_id: str
    right_id: str
    decision: str = Field(pattern="^(same|different)$")

class PreferencesRequest(BaseModel):
    payload: dict[str, Any]

@router.get("/product/receipts/{receipt_id}/image")
def receipt_image(receipt_id: str, current: Actor = Depends(actor)) -> Response:
    asset = advanced.asset(current.tenant_id, receipt_id)
    if asset is None:
        raise HTTPException(404, "Receipt image not found")
    return Response(asset.content, media_type=asset.content_type,
                    headers={"Content-Disposition": f'inline; filename="{asset.filename}"',
                             "Cache-Control": "private, no-store"})

@router.get("/product/receipts/{receipt_id}/ocr-boxes")
def receipt_boxes(receipt_id: str, current: Actor = Depends(actor)) -> dict[str, Any]:
    asset = advanced.asset(current.tenant_id, receipt_id)
    if asset is None:
        raise HTTPException(404, "Receipt image not found")
    return {"receipt_id": receipt_id, "boxes": asset.boxes}

@router.get("/product/receipts/{receipt_id}/history")
def receipt_history(receipt_id: str, current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": advanced.history(current.tenant_id, receipt_id)}

@router.get("/product/saved-views")
def saved_views(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": advanced.views(current.tenant_id)}

@router.post("/product/saved-views", status_code=201)
def create_saved_view(body: SavedViewRequest, current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return advanced.create_view(current.tenant_id, body.name, body.filters,
                                    body.shared, body.pinned)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.delete("/product/saved-views/{view_id}")
def delete_saved_view(view_id: str, current: Actor = Depends(actor)) -> dict[str, Any]:
    if not advanced.delete_view(current.tenant_id, view_id):
        raise HTTPException(404, "Saved view not found")
    return {"status": "deleted", "view_id": view_id}

@router.get("/product/notifications")
def list_notifications(include_archived: bool = False,
                       current: Actor = Depends(actor)) -> dict[str, Any]:
    items = advanced.notifications(current.tenant_id, include_archived)
    return {"items": items, "unread_count": sum(not item["read"] for item in items)}

@router.patch("/product/notifications/{notification_id}")
def update_notification(notification_id: str, body: NotificationUpdateRequest,
                        current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return advanced.update_notification(current.tenant_id, notification_id,
                                            body.read, body.archived)
    except KeyError as exc:
        raise HTTPException(404, "Notification not found") from exc

@router.post("/product/notifications/read-all")
def read_all_notifications(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"updated": advanced.mark_all_read(current.tenant_id)}

@router.get("/product/automation-rules")
def list_automation_rules(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": advanced.rules(current.tenant_id)}

@router.post("/product/automation-rules", status_code=201)
def create_automation_rule(body: AutomationRuleRequest,
                           current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return advanced.create_rule(current.tenant_id, body.name, body.conditions,
                                    body.actions, body.priority)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/product/automation-rules/preview")
def preview_automation_rule(body: AutomationRuleRequest,
                            current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"matching_receipts": advanced.rule_preview(current.tenant_id, body.conditions)}

@router.get("/product/duplicates")
def duplicate_candidates(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": advanced.duplicates(current)}

@router.post("/product/duplicates/decision")
def duplicate_decision(body: DuplicateDecisionRequest,
                       current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        result = advanced.decide_duplicate(current.tenant_id, body.left_id,
                                           body.right_id, body.decision)
        advanced.record_history(current, body.left_id, "duplicate." + body.decision,
                                None, {"other_receipt_id": body.right_id})
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get("/product/preferences")
def get_preferences(current: Actor = Depends(actor)) -> dict[str, Any]:
    return advanced.preferences(current.tenant_id, current.role)

@router.put("/product/preferences")
def save_preferences(body: PreferencesRequest,
                     current: Actor = Depends(actor)) -> dict[str, Any]:
    return advanced.save_preferences(current.tenant_id, current.role, body.payload)

@router.get("/product/export-runs")
def export_runs(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": advanced.exports(current.tenant_id)}

@router.post("/product/export-runs", status_code=201)
def create_export_run(body: ExportRequest, current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        result = service.export(current, body.connection_id, body.receipt_ids)
        return advanced.record_export(current.tenant_id, "connection",
                                      len(body.receipt_ids), result["exported"], [])
    except KeyError as exc:
        return advanced.record_export(current.tenant_id, "connection",
                                      len(body.receipt_ids), 0, [str(exc)])

# ReceiptLens 1.1 accounting-readiness API
accounting = AccountingWorkspace(service)

class LineItemsRequest(BaseModel):
    items: list[dict[str, Any]]
    expected_version: int

class ApprovalFlowRequest(BaseModel):
    name: str
    definition: dict[str, Any]

class ApprovalSimulationRequest(BaseModel):
    definition: dict[str, Any]
    receipt: dict[str, Any]

class ExportPreparationRequest(BaseModel):
    receipt_ids: list[str]
    connection_id: str | None = None

class InboundEmailRequest(BaseModel):
    sender: str
    subject: str
    attachments: list[dict[str, Any]] = []

class RecurringFeedbackRequest(BaseModel):
    merchant: str
    is_subscription: bool

class ExchangeRateRequest(BaseModel):
    base: str
    quote: str
    rate: float
    rate_date: str
    source: str = "manual"

class ConversionRequest(BaseModel):
    amount: float
    base: str
    quote: str
    rate_date: str | None = None

class PermissionRequest(BaseModel):
    role: str
    permissions: list[str]

@router.put("/product/receipts/{receipt_id}/line-items")
def update_line_items(receipt_id: str, body: LineItemsRequest,
                      current: Actor = Depends(actor)) -> dict[str, Any]:
    if current.role not in {"admin", "reviewer"}:
        raise HTTPException(403, "Reviewer role required")
    try:
        result = accounting.update_line_items(current, receipt_id, body.items,
                                              body.expected_version)
        advanced.record_history(current, receipt_id, "line_items.updated",
                                result.pop("before"), result["line_items"])
        return result
    except KeyError as exc:
        raise HTTPException(404, "Receipt not found") from exc
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get("/product/receipts/{receipt_id}/validation")
def validate_receipt_accounting(receipt_id: str, connection_id: str | None = None,
                                current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return accounting.validate(current, receipt_id, connection_id)
    except KeyError as exc:
        raise HTTPException(404, "Receipt not found") from exc

@router.get("/product/approval-flows")
def list_approval_flows(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": accounting.approval_flows(current.tenant_id)}

@router.post("/product/approval-flows", status_code=201)
def create_approval_flow(body: ApprovalFlowRequest,
                         current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return accounting.create_approval_flow(current, body.name, body.definition)
    except PermissionError as exc:
        raise HTTPException(403, "Admin role required") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/product/approval-flows/simulate")
def simulate_approval_flow(body: ApprovalSimulationRequest,
                           current: Actor = Depends(actor)) -> dict[str, Any]:
    return accounting.simulate_approval(current.tenant_id, body.definition, body.receipt)

@router.get("/product/export-preparations")
def list_export_preparations(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": accounting.export_preparations(current.tenant_id)}

@router.post("/product/export-preparations", status_code=201)
def create_export_preparation(body: ExportPreparationRequest,
                              current: Actor = Depends(actor)) -> dict[str, Any]:
    return accounting.prepare_export(current, body.receipt_ids, body.connection_id)

@router.get("/product/inbound-emails")
def list_inbound_emails(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": accounting.emails(current.tenant_id),
            "address": f"receipts+{current.tenant_id}@receiptlens.local"}

@router.post("/product/inbound-emails", status_code=201)
def receive_inbound_email(body: InboundEmailRequest,
                          current: Actor = Depends(actor)) -> dict[str, Any]:
    return accounting.receive_email(current.tenant_id, body.sender, body.subject,
                                    body.attachments)

@router.get("/product/recurring-expenses")
def recurring_expenses(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": accounting.recurring(current.tenant_id)}

@router.post("/product/recurring-expenses/feedback")
def save_recurring_feedback(body: RecurringFeedbackRequest,
                            current: Actor = Depends(actor)) -> dict[str, Any]:
    return accounting.recurring_feedback(current.tenant_id, body.merchant,
                                         body.is_subscription)

@router.post("/product/exchange-rates", status_code=201)
def set_exchange_rate(body: ExchangeRateRequest,
                      current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return accounting.set_rate(current, body.base, body.quote, body.rate,
                                   body.rate_date, body.source)
    except PermissionError as exc:
        raise HTTPException(403, "Admin role required") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.post("/product/currency/convert")
def convert_currency(body: ConversionRequest,
                     current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return accounting.convert(current.tenant_id, body.amount, body.base,
                                  body.quote, body.rate_date)
    except KeyError as exc:
        raise HTTPException(404, "Exchange rate not found") from exc

@router.get("/product/permissions")
def permissions(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"roles": accounting.permission_matrix(current.tenant_id)}

@router.put("/product/permissions")
def update_permissions(body: PermissionRequest,
                       current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return accounting.set_permissions(current, body.role, body.permissions)
    except PermissionError as exc:
        raise HTTPException(403, "Admin role required") from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get("/product/diagnostics")
def diagnostics(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {
        "version": "1.3.0", "database": "ok",
        "receipt_count": service.search_receipts(current, limit=1)["total"],
        "failed_jobs": sum(1 for job in service.list_jobs(current) if job["status"] == "failed"),
        "pwa": True, "ocr": "configured",
    }

@router.get("/product/diagnostics/bundle")
def diagnostic_bundle(current: Actor = Depends(actor)) -> Response:
    if current.role != "admin":
        raise HTTPException(403, "Admin role required")
    content = accounting.diagnostic_zip(current.tenant_id, "1.3.0")
    return Response(content, media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=receiptlens-diagnostics.zip",
                             "Cache-Control": "private, no-store"})
