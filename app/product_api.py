"""HTTP and HTML adapters for the six ReceiptLens product features."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from app.accounting_workspace import AccountingWorkspace
from app.advanced_workspace import AdvancedWorkspace, extract_ocr_boxes
from app.ocr import ConfidenceReceipt, parse_receipt_with_confidence
from app.product_service import Actor, ProductConflict, ProductService
from app.vision_ocr import SOURCE_TESSERACT, SOURCE_VISION, parse_receipt_with_vision

router = APIRouter()
service = ProductService(os.getenv("RECEIPTLENS_PRODUCT_DB", ":memory:"))
advanced = AdvancedWorkspace(service)


def actor(x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
          x_role: str | None = Header(default=None, alias="X-Role")) -> Actor:
    """Strict auth for product-workspace endpoints (SEC-003).

    Tenant and role headers are REQUIRED: a missing/blank tenant yields 401
    and an unrecognised role yields 403. Previously this defaulted to
    demo/admin, letting anyone act as an admin without headers.
    """
    if x_tenant_id is None or not x_tenant_id.strip():
        raise HTTPException(401, "Tenant identity is required")
    if x_role is None or x_role not in {"admin", "reviewer", "integrator"}:
        raise HTTPException(403, "Unknown role")
    return Actor(x_tenant_id.strip(), x_role)


def _as_bool(value: str | None) -> bool:
    """Parse a form-field boolean (1/true/yes/on => True)."""
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _ai_extraction(parsed: ConfidenceReceipt) -> dict[str, Any]:
    """Render a parsed receipt as the frontend AI-mode extraction payload.

    Mirrors the ``AiExtraction`` contract in frontend/lib/types.ts: the
    merchant field is keyed ``merchant`` (the stored receipt uses ``vendor``).
    """
    return {
        "merchant": parsed.merchant,
        "date": parsed.date,
        "total": parsed.total,
        "tax": parsed.tax,
        "currency": parsed.currency,
        "line_items": [{"name": item.name, "price": item.price} for item in parsed.items],
        "confidence": dict(parsed.confidence),
    }


class CorrectionRequest(BaseModel):
    changes: dict[str, Any]
    action: str = Field(pattern="^(save|complete)$")

class MemberRequest(BaseModel):
    email: str = Field(min_length=3)
    role: str

class ApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class ConnectionRequest(BaseModel):
    """Connection creation request.

    ``extra="forbid"`` prevents the FastAPI validation error from echoing
    arbitrary fields back (e.g. a client_secret sent inside ``config`` would
    otherwise appear verbatim in the 422 response — SEC-001).
    """
    model_config = ConfigDict(extra="forbid")

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
async def upload_receipt(
    file: UploadFile = File(...),
    ai_scan: str | None = Form(default=None, description="Enable AI-mode OCR (vision LLM with Tesseract fallback)"),
    current: Actor = Depends(actor),
) -> dict[str, Any]:
    if file.content_type and not file.content_type.startswith("image/"): raise HTTPException(415, "An image file is required")
    data = await file.read()
    if not data: raise HTTPException(422, "The uploaded file is empty")
    ai_mode = _as_bool(ai_scan)
    try:
        if ai_mode:
            parsed = parse_receipt_with_vision(data)
        else:
            parsed = parse_receipt_with_confidence(data)
    except Exception as exc:
        if not ai_mode:
            raise HTTPException(422, "Receipt processing failed") from exc
        # Vision path raised unexpectedly; fall back to the classic pipeline so
        # the user still gets an extraction (frontend shows the friendly notice).
        try:
            parsed = parse_receipt_with_confidence(data)
        except Exception as fallback_exc:
            raise HTTPException(422, "Receipt processing failed") from fallback_exc
    result = service.create_receipt(current, parsed, file.filename or "receipt")
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
    if ai_mode:
        source = str((parsed.confidence or {}).get("source") or SOURCE_TESSERACT)
        result["source"] = source
        if source == SOURCE_VISION:
            result["ai_result"] = _ai_extraction(parsed)
            try:
                result["tesseract_result"] = _ai_extraction(parse_receipt_with_confidence(data))
            except Exception:  # noqa: BLE001 - comparison OCR is best-effort
                result["tesseract_result"] = None
        else:
            result["tesseract_result"] = _ai_extraction(parsed)
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
    except ProductConflict as exc:raise HTTPException(409,{"code":"stale_version","message":str(exc)})

@router.get("/product/review-items")
def reviews(confidence_field: str | None = None, confidence_lt: float | None = None,
            readiness: str | None = None, sort: str = "created_asc", limit: int = 50,
            offset: int = 0, current: Actor = Depends(actor)) -> dict[str, Any]:
    try:
        return service.list_reviews(current, confidence_field, confidence_lt, readiness, sort, limit, offset)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

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

@router.get("/product/receipts/{receipt_id}")
def get_receipt(receipt_id: str, current: Actor = Depends(actor)) -> dict[str, Any]:
    """Return a single tenant receipt (same shape as one search item)."""
    try:
        return service.get_receipt(current, receipt_id)
    except KeyError as exc:
        raise HTTPException(404, "Receipt not found") from exc

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
from app.automation_service import AutomationService
from app.export_workflow import ExportWorkflow
from app.inbox_service import InboxService
from app.quality_service import QualityService

export_workflow = ExportWorkflow(service, accounting)
quality_service = QualityService(service)
automation_service = AutomationService(service, advanced)
inbox_service = InboxService(service)

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
    try: return export_workflow.prepare(current, body.receipt_ids, body.connection_id)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc

@router.get("/product/inbound-emails")
def list_inbound_emails(current: Actor = Depends(actor)) -> dict[str, Any]:
    return {"items": inbox_service.list(current.tenant_id),
            "address": f"receipts+{current.tenant_id}@receiptlens.local"}

@router.post("/product/inbound-emails", status_code=201)
def receive_inbound_email(body: InboundEmailRequest,
                          current: Actor = Depends(actor)) -> dict[str, Any]:
    """Ingest an inbound email into the tenant's inbox.

    Auth-required (SEC-002): without the tenant/role headers the request is
    rejected — previously anyone could POST emails into any tenant's inbox.
    """
    if current.role not in ("admin", "integrator"):
        raise HTTPException(403, "Admin or integrator role required")
    try: return inbox_service.receive(current.tenant_id, body.sender, body.subject, body.attachments)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc


@router.get("/product/inbound-emails/{email_id}")
def inbound_email_detail(email_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try:return inbox_service.get(current.tenant_id,email_id)
    except KeyError as exc:raise HTTPException(404,"Email not found") from exc
@router.post("/product/inbound-emails/{email_id}/attachments/{attachment_id}/retry")
def retry_inbound_attachment(email_id:str,attachment_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try:return inbox_service.retry(current.tenant_id,email_id,attachment_id)
    except KeyError as exc:raise HTTPException(404,"Attachment not found") from exc
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

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


class ExportCommandRequest(BaseModel):
    preparation_id: str
    acknowledged_warning_receipt_ids: list[str] = []
class BenchmarkRunRequest(BaseModel):
    manifest_name: str
    cases: list[dict[str, Any]]
class ConfidenceProfileRequest(BaseModel):
    benchmark_report_id: str
    thresholds: dict[str, float]
class AutomationPreviewV2(BaseModel):
    version: int
    receipt_ids: list[str] | None = None
class AutomationActivate(BaseModel):
    version: int
    preview_token: str
class AutomationRunRequest(BaseModel):
    version: int
    receipt_ids: list[str]
class RollbackRequest(BaseModel):
    eligible_receipt_ids: list[str]

@router.post("/product/export-commands", status_code=201)
def execute_export_command(body: ExportCommandRequest, idempotency_key: str = Header(alias="Idempotency-Key"), current: Actor = Depends(actor)) -> dict[str, Any]:
    try:return export_workflow.execute(current,body.preparation_id,body.acknowledged_warning_receipt_ids,idempotency_key)
    except KeyError as exc:raise HTTPException(404,"Preparation not found") from exc
    except RuntimeError as exc:raise HTTPException(409,{"code":"stale_preparation","message":str(exc)}) from exc
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
@router.get("/product/export-runs/{run_id}")
def export_run_detail(run_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try:return export_workflow.run(current.tenant_id,run_id)
    except KeyError as exc:raise HTTPException(404,"Export run not found") from exc
@router.get("/product/export-runs/{run_id}/artifact")
def export_run_artifact(run_id:str,current:Actor=Depends(actor))->Response:
    try:return Response(export_workflow.artifact(current.tenant_id,run_id),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=receiptlens-{run_id}.csv"})
    except KeyError as exc:raise HTTPException(404,"Export run not found") from exc
@router.get("/product/receipts/{receipt_id}/audit")
def receipt_audit(receipt_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    row=service._db.execute("SELECT receipt_id FROM receipts WHERE tenant_id=? AND receipt_id=?",(current.tenant_id,receipt_id)).fetchone()
    if not row:raise HTTPException(404,"Receipt not found")
    return {"receipt_id":receipt_id,"events":advanced.history(current.tenant_id,receipt_id)}
@router.post("/product/quality/benchmarks/run",status_code=201)
def run_benchmark(body:BenchmarkRunRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return quality_service.evaluate(current,body.manifest_name,body.cases)
    except PermissionError as exc:raise HTTPException(403,"Admin role required") from exc
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
@router.get("/product/quality/benchmarks/{report_id}")
def benchmark_report(report_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try:return quality_service.report(current.tenant_id,report_id)
    except KeyError as exc:raise HTTPException(404,"Benchmark report not found") from exc
@router.post("/product/quality/confidence-profiles",status_code=201)
def publish_profile(body:ConfidenceProfileRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return quality_service.publish(current,body.benchmark_report_id,body.thresholds)
    except PermissionError as exc:raise HTTPException(403,"Admin role required") from exc
    except KeyError as exc:raise HTTPException(404,"Benchmark report not found") from exc
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
@router.get("/product/quality/confidence-profiles/active")
def active_profile(current:Actor=Depends(actor))->dict[str,Any]:return {"profile":quality_service.active(current.tenant_id)}
@router.post("/product/automation-rules/{rule_id}/preview")
def preview_rule_version(rule_id:str,body:AutomationPreviewV2,current:Actor=Depends(actor))->dict[str,Any]:
    try:return automation_service.preview(current,rule_id,body.version,body.receipt_ids)
    except KeyError as exc:raise HTTPException(404,"Rule not found") from exc
@router.post("/product/automation-rules/{rule_id}/activate")
def activate_rule(rule_id:str,body:AutomationActivate,current:Actor=Depends(actor))->dict[str,Any]:
    try:return automation_service.activate(current,rule_id,body.version,body.preview_token)
    except KeyError as exc:raise HTTPException(404,"Rule not found") from exc
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc
@router.post("/product/automation-rules/{rule_id}/runs",status_code=201)
def run_rule(rule_id:str,body:AutomationRunRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return automation_service.run(current,rule_id,body.version,body.receipt_ids)
    except KeyError as exc:raise HTTPException(404,"Rule not found") from exc
@router.get("/product/automation-rules/{rule_id}/runs")
def automation_rule_runs(rule_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try: automation_service._rule(current.tenant_id,rule_id)
    except KeyError as exc: raise HTTPException(404,"Rule not found") from exc
    rows=service._db.execute("SELECT run_id,status,summary_json,created_at,completed_at FROM automation_runs WHERE tenant_id=? AND rule_id=? ORDER BY created_at DESC",(current.tenant_id,rule_id)).fetchall()
    return {"items":[{"run_id":r["run_id"],"status":r["status"],"summary":json.loads(r["summary_json"]),"created_at":r["created_at"],"completed_at":r["completed_at"]} for r in rows]}
@router.get("/product/automation-runs/{run_id}")
def automation_run(run_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try:return automation_service.detail(current.tenant_id,run_id)
    except KeyError as exc:raise HTTPException(404,"Run not found") from exc
@router.post("/product/automation-runs/{run_id}/rollback-preview")
def rollback_preview(run_id:str,current:Actor=Depends(actor))->dict[str,Any]:
    try:return automation_service.rollback_preview(current.tenant_id,run_id)
    except KeyError as exc:raise HTTPException(404,"Run not found") from exc
@router.post("/product/automation-runs/{run_id}/rollback")
def rollback_run(run_id:str,body:RollbackRequest,current:Actor=Depends(actor))->dict[str,Any]:
    try:return automation_service.rollback(current,run_id,body.eligible_receipt_ids)
    except KeyError as exc:raise HTTPException(404,"Run not found") from exc

# QuickBooks connected-workflow completion API
from app.accounting_projection import AccountingProjectionService
from app.connection_service import ConnectionService
from app.credential_store import CredentialStore
from app.intuit_oauth import OAuthConfigError


def _credential_store():
    try:
        return CredentialStore()
    except ValueError as exc:
        raise HTTPException(503, {'code': 'credential_store_unavailable', 'message': str(exc)}) from exc


def _connections():
    return ConnectionService(service, _credential_store())


projection_service = AccountingProjectionService(service)

class OAuthStartRequest(BaseModel):
    return_path: str = '/integrations'
class MappingBody(BaseModel):
    expense_account_ref: str
    tax_strategy: str = 'exclusive'
class ProjectionRefreshBody(BaseModel):
    reporting_currency: str

@router.post('/product/connections/quickbooks/oauth/start', status_code=201)
def qbo_oauth_start(body: OAuthStartRequest, current: Actor = Depends(actor)):
    try:
        result = _connections().start_oauth(current, body.return_path)
        return {'authorization_url': result['authorization_url'], 'state_expires_at': result['state_expires_at']}
    except PermissionError as exc:
        raise HTTPException(403, 'Admin role required') from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.api_route('/product/connections/quickbooks/oauth/callback', methods=['GET', 'POST'], status_code=201, name='qbo_oauth_callback')
def qbo_oauth_callback(state: str = Query(min_length=8), code: str = Query(min_length=1), realmId: str = Query(default='', alias='realmId')):
    """Complete a live QuickBooks Online OAuth flow from Intuit's redirect.

    Intuit redirects the browser back to this route with ``state``, ``code``
    and ``realmId``. The tenant is derived from the single-use state token;
    the authorization code is exchanged for tokens at Intuit's fixed token
    endpoint and stored encrypted. No credential material is ever returned
    in the response.
    """
    if not realmId:
        raise HTTPException(422, {'code': 'realm_required', 'message': 'realmId is required'})
    try:
        cs = _connections()
        cs.validate_state_token(state)
        cs.complete_live_oauth(state, code, realmId)
    except ValueError as exc:
        raise HTTPException(422, {'code': str(exc), 'message': 'Invalid or expired OAuth state'}) from exc
    except OAuthConfigError as exc:
        raise HTTPException(502, {'code': 'oauth_exchange_failed', 'message': str(exc)}) from exc
    return {'status': 'connected', 'redirect': '/integrations'}


@router.post('/product/connections/{connection_id}/refresh')
def refresh_provider_connection(connection_id: str, current: Actor = Depends(actor)):
    """Rotate an expiring access token via Intuit's refresh flow."""
    try:
        _, refreshed = _connections().refresh_if_needed(current, connection_id)
    except KeyError as exc:
        raise HTTPException(404, 'Connection not found') from exc
    except (ValueError, OAuthConfigError) as exc:
        # A failed Intuit refresh (invalid/expired refresh token) or a missing
        # refresh token both mean the user must re-authorize. The service has
        # already flipped the connection to reauthorization_required.
        raise HTTPException(409, {'code': 'reauthorization_required', 'message': str(exc)}) from exc
    return {'status': 'refreshed' if refreshed else 'not_needed'}


@router.post('/product/provider-mappings/validate')
def validate_provider_mapping(body:MappingBody,current:Actor=Depends(actor)):
    if current.role!='admin': raise HTTPException(403,'Admin role required')
    if not body.expense_account_ref.strip(): raise HTTPException(422,{'field':'expense_account_ref','code':'required'})
    return {'valid':True,'mapping':body.model_dump()}

@router.get('/product/receipts/{receipt_id}/accounting-projection')
def get_accounting_projection(receipt_id:str,current:Actor=Depends(actor)):
    row=service._db.execute('SELECT payload_json,stale FROM receipt_accounting_projections WHERE tenant_id=? AND receipt_id=?',(current.tenant_id,receipt_id)).fetchone()
    if not row: raise HTTPException(404,'Projection not found')
    return {**json.loads(row['payload_json']),'stale':bool(row['stale'])}

@router.post('/product/receipts/{receipt_id}/accounting-projection/refresh')
def refresh_accounting_projection(receipt_id:str,body:ProjectionRefreshBody,current:Actor=Depends(actor)):
    try:return projection_service.refresh(current,receipt_id,body.reporting_currency.upper())
    except KeyError as exc: raise HTTPException(404,str(exc)) from exc

@router.get('/product/receipts/{receipt_id}/provider-preview')
def provider_preview(receipt_id:str,receipt_version:int,mapping_version:int,current:Actor=Depends(actor)):
    if current.role not in {'admin','reviewer'}: raise HTTPException(403,'Reviewer role required')
    try:return projection_service.preview(current,receipt_id,receipt_version,mapping_version,{'expense_account_ref':'configured'})
    except (KeyError,RuntimeError) as exc: raise HTTPException(409,str(exc)) from exc

class MappingSaveBody(BaseModel):
    expense_account_ref: str
    tax_strategy: str = 'exclusive'
    snapshot_hash: str

@router.get('/product/provider-connections')
def provider_connections(current:Actor=Depends(actor)):
    return {'items':_connections().list_connections(current)}

@router.get('/product/provider-connections/{connection_id}')
def provider_connection_detail(connection_id:str,current:Actor=Depends(actor)):
    try:return _connections().get(current,connection_id)
    except KeyError as exc:raise HTTPException(404,'Connection not found') from exc

@router.post('/product/connections/{connection_id}/disconnect')
def disconnect_provider(connection_id:str,current:Actor=Depends(actor)):
    try:return _connections().disconnect(current,connection_id)
    except PermissionError as exc:raise HTTPException(403,'Admin role required') from exc
    except KeyError as exc:raise HTTPException(404,'Connection not found') from exc

@router.post('/product/connections/{connection_id}/mappings',status_code=201)
def save_provider_mapping(connection_id:str,body:MappingSaveBody,current:Actor=Depends(actor)):
    if current.role!='admin':raise HTTPException(403,'Admin role required')
    if not body.expense_account_ref.strip():raise HTTPException(422,{'field':'expense_account_ref','code':'required'})
    try:return _connections().save_mapping(current,connection_id,{'expense_account_ref':body.expense_account_ref,'tax_strategy':body.tax_strategy},body.snapshot_hash)
    except KeyError as exc:raise HTTPException(404,'Connection not found') from exc

@router.get('/product/connections/{connection_id}/mappings/current')
def current_provider_mapping(connection_id:str,current:Actor=Depends(actor)):
    try:return _connections().current_mapping(current,connection_id)
    except KeyError as exc:raise HTTPException(404,'Mapping not found') from exc
