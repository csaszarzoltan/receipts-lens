import html
import json
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.accountant_invite import invite_store
from app.credential_store import get_credential_store
from app.product_api import Actor, actor, service
from app.subscriptions_api import is_pro
from app.sync_service import SyncService

router = APIRouter()
sync_service = SyncService(service)
states: dict[str, dict] = {}


class SyncBody(BaseModel):
    date_from: str
    date_to: str


class RevokeBody(BaseModel):
    token: str


def gate(c: Actor) -> None:
    if not is_pro(c.tenant_id):
        raise HTTPException(402, {"code": "pro_required", "message": "Pro required - $5/mo"})


@router.get("/api/v1/integrations")
def connections(current: Actor = Depends(actor)):
    return {"connections": sync_service.list_connections(current.tenant_id)}


@router.get("/api/v1/integrations/{provider}/start")
def start(provider: str, current: Actor = Depends(actor)):
    gate(current)
    if provider not in {"qbo", "xero"}:
        raise HTTPException(404, "Unknown provider")
    state = secrets.token_urlsafe(24)
    states[state] = {
        "tenant": current.tenant_id,
        "provider": provider,
        "expires": datetime.now(UTC) + timedelta(minutes=10),
    }
    base = (
        "https://appcenter.intuit.com/connect/oauth2"
        if provider == "qbo"
        else "https://login.xero.com/identity/connect/authorize"
    )
    res = RedirectResponse(base + "?state=" + state)
    res.set_cookie("receiptlens_sync_state", state, httponly=True, samesite="lax", max_age=600)
    return res


@router.get("/api/v1/integrations/{provider}/callback")
def callback(provider: str, request: Request, code: str, state: str):
    x = states.pop(state, None)
    cookie = request.cookies.get("receiptlens_sync_state")
    if (
        not cookie
        or not secrets.compare_digest(cookie, state)
        or not x
        or x["provider"] != provider
        or x["expires"] <= datetime.now(UTC)
    ):
        raise HTTPException(400, "Invalid OAuth state")
    # Store external_id encrypted when RECEIPTLENS_CREDENTIAL_KEY is set (Fernet/AES-GCM),
    # plain fallback for dev (no key). ADR-006: "Fernet (CREDENTIAL_KEY)".
    cred = get_credential_store()
    external_id = code[:64]
    if cred is not None:
        try:
            external_id = cred.encrypt({"code": code[:64], "provider": provider})
        except Exception:
            external_id = code[:64]
    with service._db:
        service._db.execute(
            "INSERT OR REPLACE INTO integration_connections VALUES(?,?,?,?,?,?)",
            (
                x["tenant"],
                provider,
                provider.upper(),
                external_id,
                "connected",
                datetime.now(UTC).isoformat(),
            ),
        )
    return RedirectResponse("/integrations")


@router.post("/api/v1/integrations/{provider}/sync")
def sync(provider: str, body: SyncBody, current: Actor = Depends(actor)):
    gate(current)
    return sync_service.push(
        current.tenant_id,
        provider,
        body.date_from,
        body.date_to,
        lambda b: [{"Id": x["receipt_id"]} for x in b],
    ).__dict__


@router.get("/api/v1/accountant/invite")
def invite(request: Request, current: Actor = Depends(actor)):
    gate(current)
    x = invite_store.create_invite(current.tenant_id)
    return {"url": str(request.base_url).rstrip("/") + "/accountant/" + x["token"], **x}


@router.post("/api/v1/accountant/invite/revoke")
def revoke(body: RevokeBody, current: Actor = Depends(actor)):
    gate(current)
    return {"revoked": invite_store.revoke_invite(body.token, current.tenant_id)}


@router.get("/accountant/{token}", response_class=HTMLResponse)
def accountant(token: str):
    x = invite_store.resolve_invite(token)
    if not x:
        raise HTTPException(404, "Invite expired or invalid")
    rows = service._db.execute(
        "SELECT payload,status FROM receipts WHERE tenant_id=? ORDER BY created_at DESC",
        (x["tenant_id"],),
    ).fetchall()
    trs = "".join(
        f"<tr><td>{html.escape(str((p := json.loads(r['payload'])).get('vendor') or ''))}</td><td>{html.escape(str(p.get('date') or ''))}</td><td>{html.escape(str(p.get('total') or ''))}</td><td>{html.escape(r['status'])}</td></tr>"
        for r in rows
    )
    return HTMLResponse(
        f'<html><head><meta name="robots" content="noindex,nofollow"></head><body><h1>Receipts - read only</h1><table>{trs}</table></body></html>',
        headers={"Cache-Control": "private, no-store"},
    )
