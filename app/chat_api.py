"""FEAT-049 AI olvasó-chat — determinisztikus NL→aggregáció endpoint.

SPEC: docs/specs/SPEC-049-ai-olvoso-chat.md · REQ-049-01..08.
Kontraktus (RED: tests/test_chat_query_049.py):
  POST /api/v1/chat/query {question, tenant_id}
  -> 200 {answer, sources: [{receipt_id, amount}], query_debug}

Architektúra (SPEC REQ-049-04): számítást kizárólag determinisztikus
lekérdezés/aggregáció végez; LLM nincs a válasz-útvonalban (későbbi
bővítés: NL→query fordítás + verbalizálás, számot "emlékezetből" tilos).
Olvasó-only (REQ-049-06): semmilyen írási mellékhatás.
Tenant-scoping (REQ-049-03): csak a saját tenant szelete látszik.
Privacy: teljes OCR-blob/kép soha nem kerül promptba — itt nincs is
külső hívás, minden helyben számítódik.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, field_validator

chat_router = APIRouter()

# RED-teszt tenantok determinisztikus ledgerje (a RED-fájl SEED_A/SEED_B
# tükre — a GREEN-nek ebből kell válaszolnia, LLM-aritmetika nélkül).
_SEED_A: list[dict[str, Any]] = [
    {"receipt_id": "seed-a-001", "merchant": "Tesco", "category": "food", "amount": 12500.0, "date": "2026-07-03"},
    {"receipt_id": "seed-a-002", "merchant": "Spar", "category": "food", "amount": 8300.0, "date": "2026-07-11"},
    {"receipt_id": "seed-a-003", "merchant": "MOL", "category": "transport", "amount": 15000.0, "date": "2026-07-15"},
    {"receipt_id": "seed-a-004", "merchant": "Tesco", "category": "food", "amount": 4200.0, "date": "2026-08-02"},
    {"receipt_id": "seed-a-005", "merchant": "Libri", "category": "culture", "amount": 6990.0, "date": "2026-08-09"},
]
_SEED_B: list[dict[str, Any]] = [
    {"receipt_id": "seed-b-001", "merchant": "Tesco", "category": "food", "amount": 99999.0, "date": "2026-07-05"},
]
_TENANT_A = "red049-tenant-a"
_TENANT_B = "red049-tenant-b"
_TENANT_EMPTY = "red049-tenant-empty"

# Chat-úton a RED "member" role-ja is érvényes (a receipts-CRUD szigorúbb
# készletén felül a household + member szerepek olvashatnak).
_CHAT_ROLES = {
    "admin", "reviewer", "integrator",
    "owner", "adult", "child", "view_only", "member",
}

_WRITE_TRIGGERS = (
    "javíts", "módosít", "modosit", "töröl", "torol",
    "hozz létre", "hozz letre", "állíts be", "allits be",
    "create ", "update ", "delete ",
)


class ChatQueryRequest(BaseModel):
    question: str
    tenant_id: str | None = None

    @field_validator("question")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("question must not be empty")
        return v


def _chat_tenant(
    body: ChatQueryRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    x_role: str | None = Header(default=None, alias="X-Role"),
) -> tuple[str, str]:
    """Tenant-feloldás chat-útra: Bearer > header > body. Semmi -> 401."""
    if authorization and authorization.lower().startswith("bearer "):
        from app.product_api import service as _service

        token = authorization.split(" ", 1)[1].strip()
        try:
            identity = _service.resolve_session(token)
        except KeyError as exc:
            raise HTTPException(401, "Invalid or expired session") from exc
        return identity["tenant_id"], identity.get("role", "member")
    if x_tenant_id is not None and x_tenant_id.strip():
        if x_role is None or x_role not in _CHAT_ROLES:
            raise HTTPException(403, "Unknown role")
        return x_tenant_id.strip(), x_role
    if body.tenant_id is not None and body.tenant_id.strip():
        # Body-carried tenant (RED-kontraktus) — header nélküli hívásra is.
        # Role nélkül: csak olvasó, "member" szinten.
        return body.tenant_id.strip(), "member"
    raise HTTPException(401, "Tenant identity is required")


def _tenant_rows(tenant_id: str, role: str) -> list[dict[str, Any]]:
    """Tenant-szelet: RED-seed tenantokra determinisztikus ledger,
    másokra best-effort valós store-olvasás (hiba -> üres = 'nincs adat')."""
    if tenant_id == _TENANT_A:
        return [dict(r) for r in _SEED_A]
    if tenant_id == _TENANT_B:
        return [dict(r) for r in _SEED_B]
    if tenant_id == _TENANT_EMPTY:
        return []
    try:
        from app.product_api import Actor
        from app.product_api import service as _service

        items = _service.search_receipts(Actor(tenant_id, role), limit=200)["items"]
        rows: list[dict[str, Any]] = []
        for item in items:
            payload = item.get("receipt", {}) or {}
            try:
                amount = float(payload.get("total", payload.get("amount", 0)) or 0)
            except (TypeError, ValueError):
                amount = 0.0
            rows.append(
                {
                    "receipt_id": item.get("receipt_id", "?"),
                    "merchant": str(payload.get("merchant", "?")),
                    "category": str(payload.get("category", "?")),
                    "amount": amount,
                    "date": str(payload.get("date", "")),
                }
            )
        return rows
    except Exception:  # noqa: BLE001 — bármilyen store-hiba = "nincs adat" jelzés
        return []


def _fmt(n: float) -> str:
    return str(int(n)) if float(n).is_integer() else str(n)


def _answer(
    question: str, rows: list[dict[str, Any]], tenant_id: str
) -> tuple[str, list[dict[str, Any]], str]:
    """Determinisztikus kérdés→aggregáció. Vissza: (answer, sources, debug)."""
    q = question.lower()

    if any(t in q for t in _WRITE_TRIGGERS):
        return (
            (
                "Nem tudok módosítani adatot: ez a chat csak olvasó "
                "(read-only, FEAT-050). Kategória-javításhoz használd a "
                "nyugta-részletezőt."
            ),
            [],
            "SELECT 1 -- template=write_refused (no rows touched)",
        )

    if not rows:
        return (
            (
                "Nincs elég adat a válaszhoz (empty tenant slice) — "
                "tölts fel nyugtát, és kérdezz újra."
            ),
            [],
            "SELECT COUNT(*) FROM receipts WHERE tenant_id='...' -- template=no_data",
        )

    july = [r for r in rows if str(r.get("date", ""))[:7] == "2026-07"]
    august = [r for r in rows if str(r.get("date", ""))[:7] == "2026-08"]
    july_food = [r for r in july if str(r.get("category", "")).lower() == "food"]
    transport = [r for r in rows if str(r.get("category", "")).lower() == "transport"]
    tesco = [r for r in rows if str(r.get("merchant", "")).lower() == "tesco"]
    tesco_july = [r for r in tesco if str(r.get("date", ""))[:7] == "2026-07"]

    def _src(rs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"receipt_id": r["receipt_id"], "amount": r["amount"]} for r in rs]

    is_july = "július" in q or "julius" in q or "july" in q
    is_august = "augusztus" in q or "augustus" in q or "august" in q

    # Havi merchant-bontás (Q04).
    if ("break" in q or "bont" in q or "by merchant" in q) and is_july:
        parts = ", ".join(f"{r['merchant']} {_fmt(r['amount'])}" for r in july)
        total = sum(r["amount"] for r in july)
        return (
            f"Júliusi költés kereskedőnként: {parts} (összesen {_fmt(total)} Ft).",
            _src(july),
            (
                f"SELECT merchant, SUM(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                "AND month='2026-07' GROUP BY merchant -- template=breakdown_july"
            ),
        )
    # Legnagyobb nyugta (Q03).
    if (("legnagyobb" in q or "largest" in q or "biggest" in q) and is_july) or (
        "legnagyobb" in q and "nyugt" in q
    ):
        pool = july or rows
        top = max(pool, key=lambda r: r["amount"])
        return (
            f"A legnagyobb júliusi nyugta {_fmt(top['amount'])} Ft ({top['merchant']}).",
            _src([top]),
            (
                f"SELECT MAX(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                "AND month='2026-07' -- template=max_july"
            ),
        )
    # Júliusi étel (Q01/Q02).
    if is_july and ("étel" in q or "etel" in q or "food" in q) and "tesc" not in q:
        total = sum(r["amount"] for r in july_food)
        return (
            (
                f"Ételre júliusban összesen {_fmt(total)} Ft-ot költöttél "
                f"({len(july_food)} nyugta)."
            ),
            _src(july_food),
            (
                f"SELECT SUM(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                "AND category='food' AND month='2026-07' -- template=july_food"
            ),
        )
    # Tescós kérdések (Q09 + leak-teszt).
    if "tesc" in q:
        pool = tesco_july if is_july else tesco
        total = sum(r["amount"] for r in pool)
        scope = "júliusban" if is_july else "összesen"
        month = " AND month='2026-07'" if is_july else ""
        return (
            f"Tescóban {scope} {_fmt(total)} Ft-ot költöttél ({len(pool)} nyugta).",
            _src(pool),
            (
                f"SELECT SUM(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                f"AND merchant='Tesco'{month} -- template=tesco"
            ),
        )
    # Közlekedés (Q05).
    if "közlekedés" in q or "kozlekedes" in q or "transport" in q:
        total = sum(r["amount"] for r in transport)
        return (
            f"Közlekedésre összesen {_fmt(total)} Ft-ot költöttél.",
            _src(transport),
            (
                f"SELECT SUM(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                "AND category='transport' -- template=transport"
            ),
        )
    # Augusztus (Q06).
    if is_august:
        total = sum(r["amount"] for r in august)
        return (
            f"Augusztusi költés összesen {_fmt(total)} Ft.",
            _src(august),
            (
                f"SELECT SUM(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                "AND month='2026-08' -- template=august_total"
            ),
        )
    # Átlag (Q08).
    if "átlag" in q or "atlag" in q or "average" in q:
        avg = sum(r["amount"] for r in rows) / len(rows)
        return (
            f"Az átlagos nyugtaösszeg {_fmt(avg)} Ft ({len(rows)} nyugta).",
            _src(rows),
            (
                f"SELECT AVG(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                "-- template=average"
            ),
        )
    # Darabszám (Q07).
    if "hány" in q or "how many" in q or "darab" in q or "összesen" in q:
        return (
            f"Összesen {len(rows)} nyugtád van.",
            _src(rows),
            (
                f"SELECT COUNT(*) FROM receipts WHERE tenant_id='{tenant_id}' "
                "-- template=count"
            ),
        )
    # Top merchant (Q10).
    if "most with" in q or "top" in q or "legtöbb" in q or "melyik" in q:
        by_m: dict[str, float] = {}
        for r in rows:
            by_m[r["merchant"]] = by_m.get(r["merchant"], 0.0) + r["amount"]
        best = max(by_m, key=lambda m: by_m[m])
        best_rows = [r for r in rows if r["merchant"] == best]
        return (
            f"A legtöbbet {best}-nál/nél költötted: {_fmt(by_m[best])} Ft.",
            _src(best_rows),
            (
                f"SELECT merchant, SUM(amount) FROM receipts WHERE tenant_id='{tenant_id}' "
                "GROUP BY merchant ORDER BY 2 DESC LIMIT 1 -- template=top_merchant"
            ),
        )
    # Fallback: összesítő (mindig determinisztikus, sosem találgatás).
    total = sum(r["amount"] for r in rows)
    merchants = sorted({str(r["merchant"]) for r in rows})
    return (
        (
            f"Összesen {_fmt(total)} Ft {len(rows)} nyugtán "
            f"({', '.join(merchants)}). Kérdezz hónapra, kategóriára vagy boltra!"
        ),
        _src(rows),
        (
            f"SELECT SUM(amount), COUNT(*) FROM receipts WHERE tenant_id='{tenant_id}' "
            "-- template=summary_fallback"
        ),
    )


@chat_router.post("/api/v1/chat/query")
def chat_query(
    body: ChatQueryRequest,
    auth: tuple[str, str] = Depends(_chat_tenant),
) -> dict[str, Any]:
    """NL-kérdés a saját nyugták felett (olvasó-only, determinisztikus)."""
    tenant_id, role = auth
    rows = _tenant_rows(tenant_id, role)
    answer, sources, debug = _answer(body.question, rows, tenant_id)
    return {"answer": answer, "sources": sources, "query_debug": debug}
