from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.product_api import Actor, actor, service
from app.subscriptions_api import is_pro
from app.tax_audit import generate_tax_audit_pdf
from app.tax_service import TaxService
from app.taxonomy import TAX_CATEGORIES

router = APIRouter()
tax_service = TaxService(service)


class CatBody(BaseModel):
    vendor: str = ""
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    locale: str = "US"


class OverrideBody(BaseModel):
    tax_category: str
    locale: str = "US"


class BackfillBody(BaseModel):
    locale: str = "US"


def gate(c: Actor):
    if not is_pro(c.tenant_id):
        raise HTTPException(402, {"code": "pro_required", "message": "Pro required - $5/mo"})


@router.get("/api/v1/tax/categories")
def categories(locale: str = "US", current: Actor = Depends(actor)):
    if locale.upper() not in TAX_CATEGORIES:
        raise HTTPException(422, "locale must be US or HU")
    return {"categories": TAX_CATEGORIES[locale.upper()]}


@router.post("/api/v1/tax/categorize")
def categorize(body: CatBody, current: Actor = Depends(actor)):
    try:
        x = tax_service.categorize(body.vendor.strip(), body.line_items, body.locale)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return {
        "results": [{"name": i.get("name", body.vendor), **x} for i in (body.line_items or [{}])]
    }


@router.patch("/api/v1/receipts/{receipt_id}/tax")
def override(receipt_id: str, body: OverrideBody, current: Actor = Depends(actor)):
    gate(current)
    try:
        return tax_service.override(
            current.tenant_id, receipt_id, body.tax_category.strip(), body.locale
        )
    except KeyError as e:
        raise HTTPException(404, "Receipt not found") from e
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@router.get("/api/v1/tax/deduction")
def deduction(year: int, locale: str = "US", current: Actor = Depends(actor)):
    gate(current)
    return tax_service.deduction(current.tenant_id, year, locale)


@router.get("/api/v1/tax/audit.pdf")
def audit(year: int, locale: str = "US", current: Actor = Depends(actor)):
    gate(current)
    data = generate_tax_audit_pdf(tax_service.deduction(current.tenant_id, year, locale))
    return Response(
        data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tax-audit-{year}-{locale.upper()}.pdf"'
        },
    )


@router.post("/api/v1/tax/backfill")
def backfill(body: BackfillBody, current: Actor = Depends(actor)):
    gate(current)
    return tax_service.backfill(current.tenant_id, body.locale)
