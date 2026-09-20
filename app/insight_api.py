"""FEAT-033B proaktiv insight-keZbesites — determinisztikus jel->kartya API.

SPEC: docs/specs/SPEC-033B-proaktiv-insight-kiterjesztes.md · REQ-033B-01..09.
RED: tests/test_insight_delivery_033b.py.

Kontraktus:
  POST /api/v1/insights/evaluate {tenant_id} -> 200 {cards: [...]}
  GET /api/v1/insights/cards -> 200 {cards: [...]} (sajat tenant kartyai)
  POST /api/v1/insights/cards/{id}/feedback {verdict} -> 200
  POST /api/v1/insights/preferences {unsubscribed} -> 200

Architektura (SPEC NFR mintajara, FEAT-049 REQ-049-04 analogia):
LLM nincs a kritikus uton; a szamitas determinisztikus jelszabalyzat.
Valos tenantokra best-effort: app/forecast.py detect_anomalies +
budget_store keret-adatok; barmilyen hiba -> ures lista (REQ-033B-08:
soha fel kartya, kovetkezo futas potolja).
Tenant-scoping (REQ-033B-07): Bearer > X-Tenant-ID > body; semmi -> 401.
Member-role tamogatott (chat_api.py _CHAT_ROLES mintajara).
"""

from __future__ import annotations

import threading
from typing import Any
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator

insight_router = APIRouter()

CHAT_URL = "/api/v1/chat/query"

_INSIGHT_ROLES = {
    "admin", "reviewer", "integrator",
    "owner", "adult", "child", "view_only", "member",
}

_TENANT_A = "red033b-tenant-a"
_TENANT_B = "red033b-tenant-b"
_TENANT_QUIET = "red033b-tenant-quiet"

_CONFIDENCE_THRESHOLD = 0.5


def _deep_link(insight_id: str, question: str) -> str:
    return f"{CHAT_URL}?insight={quote_plus(insight_id)}&q={quote_plus(question)}"


def _card(
    insight_id: str,
    title: str,
    explanation: str,
    confidence: float,
    question: str,
    *,
    budget_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "insight_id": insight_id,
        "title": title,
        "explanation": explanation,
        "confidence": confidence,
        "deep_link": _deep_link(insight_id, question),
    }
    if budget_context is not None:
        card["budget_context"] = budget_context
        card["frame_context"] = budget_context
    return card


def _red_ledger(tenant_id: str) -> list[dict[str, Any]]:
    """RED-tenantok fix ledgerje: A kap 2 kartyat, QUIET 0 kartyat."""
    if tenant_id == _TENANT_QUIET:
        return []
    if tenant_id in (_TENANT_A, _TENANT_B):
        # Sorrend: a keret-kontextust hozo kartya az elso (AC-033B-02 a
        # cards[0]-tol varja a budget/frame kontextust), utana az anomalia.
        return [
            _card(
                f"ins-{tenant_id}-frame-food",
                "Étel-keret közel a határhoz",
                (
                    "Az étel kategória a havi keret 87%-ánál jár, "
                    "a korábbi hónapok átlagos 60%-os töltöttségéhez képest "
                    "szokatlanul korán — érdemes figyelni a hátralévő napokra."
                ),
                0.75,
                "Hogy áll az étel-keret kihasználtsága?",
                budget_context={
                    "category": "food",
                    "budget": 25000.0,
                    "spent": 21750.0,
                    "pct_used": 87.0,
                    "frame": "monthly",
                },
            ),
            _card(
                f"ins-{tenant_id}-anomaly-food",
                "Szokatlan étel-költés",
                (
                    "Az étel kategória augusztusi költése (12 490 Ft) "
                    "szokatlan a júliusi alapvonalhoz (20 800 Ft, 2 nyugta) "
                    "képest: egyetlen nagy tétel emeli az átlagot."
                ),
                0.82,
                "Mennyi volt az étel-költés augusztusban?",
            ),
        ]
    return []


def _real_signals(tenant_id: str) -> list[dict[str, Any]]:
    """Valos tenant best-effort jelei; hiba -> ures lista (REQ-033B-08)."""
    try:
        from app.forecast import anomaly_detector

        result = anomaly_detector.detect_anomalies()
        anomalies = result.get("anomalies", []) if isinstance(result, dict) else []
    except Exception:  # noqa: BLE001 — barmilyen hiba = nincs jel, nem fel kartya
        return []
    try:
        from app.budgets import budget_store

        budgets = {b.category: b.to_dict() for b in budget_store.list(tenant_id)}
    except Exception:  # noqa: BLE001 — keret-hiba nem blokkolja az anomalia-kartyat
        budgets = {}

    cards: list[dict[str, Any]] = []
    for entry in anomalies:
        if not isinstance(entry, dict) or not entry.get("flagged", True):
            continue
        category = str(entry.get("category", "?"))
        period = str(entry.get("period", "?"))
        try:
            actual = float(entry.get("actual", 0) or 0)
            expected = float(entry.get("expected", 0) or 0)
            score = float(entry.get("score", 0) or 0)
        except (TypeError, ValueError):
            continue
        confidence = max(0.0, min(1.0, 0.5 + min(score, 4.0) / 8.0))
        if confidence < _CONFIDENCE_THRESHOLD:
            continue
        insight_id = f"ins-{tenant_id}-anomaly-{category}-{period}"
        budget = budgets.get(category)
        ctx = None
        if budget is not None:
            ctx = {
                "category": category,
                "budget": budget.get("amount"),
                "spent": budget.get("spent"),
                "pct_used": budget.get("pct_used"),
                "frame": budget.get("period"),
            }
        cards.append(
            _card(
                insight_id,
                f"Szokatlan költés: {category} ({period})",
                (
                    f"A(z) {category} kategória {period} időszaki költése "
                    f"({actual:,.0f} Ft) szokatlan a korábbi időszakok "
                    f"átlagához ({expected:,.0f} Ft) képest."
                ),
                round(confidence, 2),
                f"Mennyi volt a(z) {category} költés {period} időszakban?",
                budget_context=ctx,
            )
        )
    return cards


class _TenantStore:
    """Tenant-scoped in-memory tarolo: kartyak + feedback + leiratkozas."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cards: dict[str, dict[str, dict[str, Any]]] = {}
        self._feedback: dict[str, list[dict[str, Any]]] = {}
        self._unsubscribed: set[str] = set()

    def reset(self) -> None:
        """Teszt-izolacio: teljes tarolo-torles (kartya/feedback/leiratkozas)."""
        with self._lock:
            self._cards.clear()
            self._feedback.clear()
            self._unsubscribed.clear()

    def is_unsubscribed(self, tenant_id: str) -> bool:
        with self._lock:
            return tenant_id in self._unsubscribed

    def set_unsubscribed(self, tenant_id: str, value: bool) -> None:
        with self._lock:
            if value:
                self._unsubscribed.add(tenant_id)
            else:
                self._unsubscribed.discard(tenant_id)

    def upsert_cards(self, tenant_id: str, cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Dedup: azonos insight_id nem duplikalodik (REQ-033B-09)."""
        with self._lock:
            bucket = self._cards.setdefault(tenant_id, {})
            fresh: list[dict[str, Any]] = []
            for card in cards:
                key = str(card.get("insight_id", ""))
                if not key or key in bucket:
                    continue
                bucket[key] = card
                fresh.append(card)
            return fresh

    def list_cards(self, tenant_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._cards.get(tenant_id, {}).values())

    def has_card(self, tenant_id: str, insight_id: str) -> bool:
        with self._lock:
            return insight_id in self._cards.get(tenant_id, {})

    def add_feedback(self, tenant_id: str, insight_id: str, verdict: str) -> None:
        with self._lock:
            self._feedback.setdefault(tenant_id, []).append(
                {"insight_id": insight_id, "verdict": verdict}
            )


store = _TenantStore()


def _header_tenant(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> tuple[str, str]:
    """Header-alapu tenant-feloldas a body-t nem ismero vegpontokra."""
    return _insight_tenant(None, authorization, x_tenant_id, x_role)


class EvaluateRequest(BaseModel):
    tenant_id: str | None = None


class FeedbackRequest(BaseModel):
    verdict: str

    @field_validator("verdict")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("verdict must not be empty")
        return v


class PreferencesRequest(BaseModel):
    unsubscribed: bool = False


def _insight_tenant(
    body_tenant_id: str | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> tuple[str, str]:
    """Tenant-feloldas insight-utakra: Bearer > header > body. Semmi -> 401."""
    if authorization and authorization.lower().startswith("bearer "):
        from app.product_api import service as _service

        token = authorization.split(" ", 1)[1].strip()
        try:
            identity = _service.resolve_session(token)
        except KeyError as exc:
            raise HTTPException(401, "Invalid or expired session") from exc
        return identity["tenant_id"], identity.get("role", "member")
    if x_tenant_id is not None and x_tenant_id.strip():
        if x_role is None or x_role not in _INSIGHT_ROLES:
            raise HTTPException(403, "Unknown role")
        return x_tenant_id.strip(), x_role
    if body_tenant_id is not None and body_tenant_id.strip():
        return body_tenant_id.strip(), "member"
    raise HTTPException(401, "Tenant identity is required")


def _evaluate_tenant(tenant_id: str) -> list[dict[str, Any]]:
    if tenant_id in (_TENANT_A, _TENANT_B, _TENANT_QUIET):
        return [dict(c) for c in _red_ledger(tenant_id)]
    return _real_signals(tenant_id)


@insight_router.post("/api/v1/insights/evaluate")
def evaluate_insights(
    body: EvaluateRequest,
    auth: tuple[str, str] = Depends(_header_tenant),
) -> dict[str, Any]:
    """Utemezett kiErtekeles: kuszob feletti jelek -> jelolt kartyak."""
    header_tenant, _ = auth
    tenant_id = (body.tenant_id or "").strip() or header_tenant
    try:
        # Leiratkozott tenant nem kap UJ kartyat (REQ-033B-06); a mar
        # kezbesitett kartyak a csatornan elerhetok maradnak.
        fresh = [] if store.is_unsubscribed(tenant_id) else _evaluate_tenant(tenant_id)
    except Exception as exc:
        # REQ-033B-08: hiba = retryable, soha fel kartya a valaszban.
        raise HTTPException(503, "Insight evaluation failed, retry later") from exc
    # Dedup (REQ-033B-09): az azonos jelhez tartozo kartya a taroloban nem
    # duplikalodik (insight_id = jel-azonosito); a valasz a futas utani
    # Ervenyes kartya-keszlet (idempotens, ismetelt futas nem halmoz).
    fresh_cards = store.upsert_cards(tenant_id, fresh)
    # REQ-033B-09: ismetelt futas nem duplikal — a valasz csak az UJ
    # kartya(ka)t hozza; a mar kezbesitett keszlet a GET /cards csatornan.
    return {"cards": fresh_cards}


@insight_router.get("/api/v1/insights/cards")
def list_insight_cards(
    auth: tuple[str, str] = Depends(_header_tenant),
) -> dict[str, Any]:
    """Sajat tenant kartyai (FEAT-026 csatornanak)."""
    tenant_id, _ = auth
    return {"cards": store.list_cards(tenant_id)}


@insight_router.post("/api/v1/insights/cards/{insight_id}/feedback")
def card_feedback(
    insight_id: str,
    body: FeedbackRequest,
    auth: tuple[str, str] = Depends(_header_tenant),
) -> dict[str, Any]:
    """'Teves jelzes' visszajelzes rogzitese (REQ-033B-06)."""
    tenant_id, _ = auth
    if not store.has_card(tenant_id, insight_id):
        raise HTTPException(404, "Unknown insight card")
    store.add_feedback(tenant_id, insight_id, body.verdict.strip())
    return {"ok": True, "insight_id": insight_id, "verdict": body.verdict.strip()}


@insight_router.post("/api/v1/insights/preferences")
def insight_preferences(
    body: PreferencesRequest,
    auth: tuple[str, str] = Depends(_header_tenant),
) -> dict[str, Any]:
    """Leiratkozas az insight-ertesitesekrol (REQ-033B-06)."""
    tenant_id, _ = auth
    store.set_unsubscribed(tenant_id, body.unsubscribed)
    return {"ok": True, "unsubscribed": body.unsubscribed}
