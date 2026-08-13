"""F1.4 OCR-pontosság consumer-pivot contract — US-022 RED pre-test suite.

Szándék: TDD contract tesztek a docs/plans/consumer-pivot-2026-08-13.md
§2.2 / F1.4 acceptance kritériumaihoz (parent t_50d6b86a handoff:

  1. BUG-001 regresszió: gyenge minőségű képen a kinyert total NE legyen
     1.0 hamis érték — vagy pontos, vagy 'uncertain' jelzés.
  2. Per-receipt konfidencia-mező a parse-receipt válaszban
     (high/medium/low).
  3. Review-flow: gyenge találatnál a UI megerősítést kér, mielőtt
     elfogad (US-022 story, BDD acceptance).
  4. Legalább 1 integrációs teszt (TestClient, valós multipart upload —
     NEM mock-only).
  5. tsc --noEmit: 0 hiba (frontend/lib/types.ts konfidencia-contract).
  6. BUG-009 (2× Tesseract, 300s+ terhelten) — scope-on kívül, nincs
     teszt (a feature task explicit kizárta).

Állapot a RED fázisban (55bb212-on):
  GREEN (regressziós guard, contract már teljesül):
    - /v1/parse-receipt válasz confidence_level mező (high/medium/low)
    - BUG-001: alacsony minőségű kép -> soha total=1.0, total None +
      "low" jelzés
    - review page.tsx: bizonytalan-összeg alert + "Confirm amount" gomb
      (UI kontraktus)
    - backend store-ba mentett confidence dict (per-field)
  RED (implementáció hiányzik — a developer handoff által is
      jelzett űr, éles úton bizonyítva):
    - confidence_level NEM kerül be a product store-ba
      (app/product_service.py::_receipt_payload), így a
      /product/receipts/upload válasz receipt.confidence_level = None
    - a /product/review-items lista (amit a review UI renderel) NEM
      hordozza a confidence_level-t -> a megerősítés-gate nem tud
      élesben tüzelni
    - _ai_extraction (AiExtraction payload) NEM adja át a
      confidence_level-t -> a frontend tesseract_result/ai_result ágon
      sem jelenik meg

Run:
    PATH="$PWD/.venv/bin:$PATH" python -m pytest tests/test_us_022_ocr_confidence_contract.py -v

Eredmény: 13 GREEN (regressziós guard) + 7 RED (contract hiányzó
része — mind egyetlen gyökérokra vezethető: a store/AiExtraction
mapper nem adja át a confidence_level-t). A RED tesztek elhullnak,
amíg a store-perszisztencia el nem készül. Harness-validálva: a
minimális fix (2 sor a két mapperben) után 20/20 GREEN.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import api
from app.ocr import ConfidenceReceipt
from app.product_api import service
from tests.fixtures_bug001_images import blurry_receipt, clean_receipt, noisy_garbage

pytestmark = pytest.mark.us022

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"
REVIEW_PAGE = FRONTEND / "app" / "(app)" / "review" / "page.tsx"
TYPES = FRONTEND / "lib" / "types.ts"
PRODUCT_SERVICE = REPO_ROOT / "app" / "product_service.py"
PRODUCT_API = REPO_ROOT / "app" / "product_api.py"

VALID_LEVELS = {"high", "medium", "low"}


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(api.app)


@pytest.fixture(scope="module")
def headers() -> dict[str, str]:
    return {"X-Tenant-ID": "us022-pretest", "X-Role": "admin"}


# ---------------------------------------------------------------------------
# 1. BUG-001 regresszió (GREEN guard — contract teljesül 55bb212 óta)
# ---------------------------------------------------------------------------


def test_bug001_blurry_image_total_never_fabricated_one() -> None:
    """AC1: gyenge kép -> total SOHA nem a hamis 1.0 érték.

    Regression pin: korábban a last-numeric-line fallback stray '1'
    töredékekből gyártott total=1.0-t.
    """
    parsed = api.parse_receipt_with_confidence(blurry_receipt())
    assert parsed.total != 1.0, f"BUG-001: total=1.0 fabricálva (raw={parsed.raw_text!r})"


def test_bug001_blurry_image_flagged_uncertain() -> None:
    """AC1/AC2: ha nincs tiszta total, 'uncertain' jelzés kell — nem érték."""
    parsed = api.parse_receipt_with_confidence(blurry_receipt())
    if parsed.total is None:
        assert parsed.confidence_level == "low", "bizonytalan total -> 'low' szint kell"
    else:
        assert parsed.confidence_level in ("medium", "low"), (
            f"bizonytalan kép total={parsed.total} magabiztos szinttel"
        )


def test_bug001_noisy_garbage_low_confidence() -> None:
    """AC1: zajos kép -> 'low' konfidencia-szint."""
    parsed = api.parse_receipt_with_confidence(noisy_garbage())
    assert parsed.confidence_level == "low"


def test_bug001_clean_control_still_parses() -> None:
    """Kontroll: tiszta kép továbbra is valós totalt ad (nincs túlkorrekció)."""
    parsed = api.parse_receipt_with_confidence(clean_receipt())
    assert parsed.total is not None and parsed.total != 1.0


# ---------------------------------------------------------------------------
# 2. Konfidencia-mező a parse-receipt válaszban (GREEN guard)
# ---------------------------------------------------------------------------


def test_confidence_level_field_in_parse_receipt_response(client: TestClient) -> None:
    """AC2: /v1/parse-receipt válasz hordozza a per-receipt szintet."""
    resp = client.post(
        "/v1/parse-receipt",
        files={"file": ("clean.png", clean_receipt(), "image/png")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "confidence_level" in body, "parse-receipt válaszból hiányzik a confidence_level"
    assert body["confidence_level"] in VALID_LEVELS


def test_confidence_level_valid_values() -> None:
    """A szint a {high, medium, low} halmaz eleme."""
    parsed = api.parse_receipt_with_confidence(clean_receipt())
    assert parsed.confidence_level in VALID_LEVELS


def test_confidence_level_consistent_with_per_field_scores() -> None:
    """A szint konzisztens a per-field konfidencia-átlaggal.

    Threshold contract: >=0.85 high, >=0.60 medium, alatta low
    (app/ocr.py _CONF_LEVEL_*).
    """
    parsed = api.parse_receipt_with_confidence(clean_receipt())
    conf = parsed.confidence or {}
    values = [v for v in conf.values() if isinstance(v, (int, float))]
    if not values:
        assert parsed.confidence_level == "low"
        return
    avg = sum(values) / len(values)
    if parsed.confidence_level == "high":
        assert avg >= 0.85
    elif parsed.confidence_level == "medium":
        assert 0.60 <= avg < 0.85
    else:
        assert avg < 0.60


def test_ai_extraction_payload_contract_in_types() -> None:
    """AC2 (frontend contract): AiExtraction hordozza a confidence_level-t."""
    src = TYPES.read_text(encoding="utf-8")
    assert "ConfidenceLevel" in src
    assert "confidence_level" in src
    assert re.search(r'type\s+ConfidenceLevel\s*=\s*"high"\s*\|\s*"medium"\s*\|\s*"low"', src), (
        "ConfidenceLevel union típus hiányzik vagy eltér a high/medium/low contracttól"
    )


# ---------------------------------------------------------------------------
# 3. Review-flow megerősítés (UI contract — US-022, GREEN guard)
# ---------------------------------------------------------------------------


def test_review_ui_asks_confirmation_on_weak_match() -> None:
    """AC3: gyenge találatnál a review UI megerősítést kér (bizonytalan összeg)."""
    src = REVIEW_PAGE.read_text(encoding="utf-8")
    assert re.search(r"uncertain|bizonytalan", src, re.IGNORECASE), (
        "review UI-ból hiányzik a bizonytalan-összeg figyelmeztetés"
    )
    assert re.search(r"Confirm amount|megerősít|Erősítse meg", src, re.IGNORECASE), (
        "review UI-ból hiányzik a megerősítés-gomb"
    )


def test_review_ui_weak_gate_is_driven_by_confidence_level() -> None:
    """AC3 (kontraktus-összefüggés): a gate a confidence_level-től függ.

    A review page isWeakMatch a confidence_level (low/medium) VAGY az
    átlag < 0.6 alapján dönt — ez a UI contract gerince.
    """
    src = REVIEW_PAGE.read_text(encoding="utf-8")
    assert re.search(r"confidence_level", src), (
        "review UI weak-gate nem a confidence_level-től függ — a "
        "store-perszisztencia nélkül a megerősítés SOHA nem tüzel"
    )


# ---------------------------------------------------------------------------
# 4. Integrációs tesztek (TestClient, valós multipart upload — NEM mock-only)
# ---------------------------------------------------------------------------


def test_integration_upload_blurry_total_not_one_via_product_flow(
    client: TestClient, headers: dict[str, str]
) -> None:
    """AC4: valós multipart upload a product flow-n — BUG-001 sosem total=1.0."""
    resp = client.post(
        "/product/receipts/upload",
        headers=headers,
        files={"file": ("blurry.png", blurry_receipt(), "image/png")},
    )
    assert resp.status_code == 201, f"upload nem 201: {resp.status_code} {resp.text[:200]}"
    body = resp.json()
    assert body["receipt"]["total"] != 1.0, (
        f"BUG-001 a product flow-n: total=1.0 fabricálva ({body['receipt']})"
    )


def test_red_upload_response_carries_confidence_level(
    client: TestClient, headers: dict[str, str]
) -> None:
    """RED: a /product/receipts/upload válasz receipt-objektuma hordozza a szintet.

    A /v1/parse-receipt válasz már hordozza (GREEN guard lentebb), de a
    product upload válasz a store-payloadot adja vissza, amelyből
    hiányzik a mező (KeyError / None).
    """
    resp = client.post(
        "/product/receipts/upload",
        headers=headers,
        files={"file": ("clean.png", clean_receipt(), "image/png")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "confidence_level" in body["receipt"], (
        "upload válasz receipt-jából hiányzik a confidence_level kulcs — "
        "a store-payload nem adja át"
    )
    assert body["receipt"]["confidence_level"] in VALID_LEVELS


# ---------------------------------------------------------------------------
# RED: store-perszisztencia (a developer handoff által jelzett űr, éles
# úton bizonyítva) — ezek addig hullanak, amíg a service át nem adja
# a confidence_level-t a mentett receipt-payloadba.
# ---------------------------------------------------------------------------


def test_red_upload_persists_confidence_level(
    client: TestClient, headers: dict[str, str]
) -> None:
    """RED: a mentett receipt hordozza a confidence_level-t.

    Jelenleg a service._receipt_payload kihagyja a confidence_level-t,
    így a store-ban None — a review UI megerősítés-gate nem tud tüzelni.
    """
    resp = client.post(
        "/product/receipts/upload",
        headers=headers,
        files={"file": ("clean.png", clean_receipt(), "image/png")},
    )
    assert resp.status_code == 201
    stored = resp.json()["receipt"]
    assert stored.get("confidence_level") in VALID_LEVELS, (
        f"store-ba mentett receipt.confidence_level hiányzik (kapott: "
        f"{stored.get('confidence_level')!r}) — product_service "
        f"_receipt_payload nem adja át a szintet"
    )


def test_red_upload_blurry_persists_low_confidence(
    client: TestClient, headers: dict[str, str]
) -> None:
    """RED: gyenge kép mentett receipt-je 'low' szintet hordoz."""
    resp = client.post(
        "/product/receipts/upload",
        headers=headers,
        files={"file": ("blurry.png", blurry_receipt(), "image/png")},
    )
    assert resp.status_code == 201
    stored = resp.json()["receipt"]
    assert stored.get("confidence_level") == "low", (
        f"blurry upload mentett receipt-je nem 'low' (kapott: "
        f"{stored.get('confidence_level')!r})"
    )


def test_red_review_items_carry_confidence_level(
    client: TestClient, headers: dict[str, str]
) -> None:
    """RED: /product/review-items (a review UI adatforrása) hordozza a szintet.

    A megerősítés-gate a review page.tsx-ben item.receipt.confidence_level
    alapján dönt — ez a mező jelenleg hiányzik a listázott payloadból.
    """
    resp = client.post(
        "/product/receipts/upload",
        headers=headers,
        files={"file": ("clean.png", clean_receipt(), "image/png")},
    )
    assert resp.status_code == 201
    receipt_id = resp.json()["receipt_id"]
    items = client.get("/product/review-items", headers=headers).json()["items"]
    match = next((it for it in items if it["receipt_id"] == receipt_id), None)
    assert match is not None, "a feltöltött receipt nem szerepel a review listában"
    assert match["receipt"].get("confidence_level") in VALID_LEVELS, (
        "review-items payloadjából hiányzik a confidence_level — a review "
        "UI megerősítés-gate nem tud élesben tüzelni"
    )


def test_red_ai_extraction_carries_confidence_level(
    client: TestClient, headers: dict[str, str]
) -> None:
    """RED: az AiExtraction payload (ai_result/tesseract_result) is átadja.

    A frontend lib/types.ts szerint az AiExtraction hordozza a
    confidence_level-t, de a backend _ai_extraction kihagyja.
    """
    resp = client.post(
        "/product/receipts/upload",
        headers=headers,
        files={"file": ("clean.png", clean_receipt(), "image/png")},
        data={"ai_scan": "true"},
    )
    assert resp.status_code == 201
    body = resp.json()
    extraction = body.get("ai_result") or body.get("tesseract_result") or {}
    assert extraction.get("confidence_level") in VALID_LEVELS, (
        f"AiExtraction payloadból hiányzik a confidence_level "
        f"(extraction kulcsok: {sorted(extraction.keys())})"
    )


def test_red_service_payload_maps_confidence_level() -> None:
    """RED (szerkezeti): a store-payload mapper átadja a szintet.

    A _receipt_payload statikus metódus dict-et épít a mentéshez —
    a confidence_level kulcsnak szerepelnie kell benne.
    """
    src = PRODUCT_SERVICE.read_text(encoding="utf-8")
    assert "confidence_level" in src, (
        "app/product_service.py nem hivatkozik a confidence_level-re — "
        "a mentett receipt soha nem fogja hordozni"
    )
    assert "confidence" in src  # a per-field dict már átmegy; ez maradjon is


def test_red_ai_extraction_maps_confidence_level() -> None:
    """RED (szerkezeti): _ai_extraction átadja a szintet."""
    src = PRODUCT_API.read_text(encoding="utf-8")
    assert "confidence_level" in src, (
        "app/product_api.py _ai_extraction nem adja át a confidence_level-t"
    )


# ---------------------------------------------------------------------------
# BUG-009 scope-guard: NEM része az F1.4-nek (feature task 6. pont)
# ---------------------------------------------------------------------------


def test_bug009_out_of_scope_guard() -> None:
    """BUG-009 (2× Tesseract, 300s+ terhelten) marad nyitott — nincs tesztje.

    Ez a guard dokumentálja, hogy a hiány SZÁNDÉKOS: a feature task
    explicit kizárta a scope-ból.
    """
    assert True  # szándékos scope-döntés rögzítése


# ---------------------------------------------------------------------------
# Mellék-interface guards (GREEN)
# ---------------------------------------------------------------------------


def test_parsed_receipt_is_confidence_receipt() -> None:
    """A konfidencia-flow ConfidenceReceipt-et ad vissza (contract-típus)."""
    parsed = api.parse_receipt_with_confidence(clean_receipt())
    assert isinstance(parsed, ConfidenceReceipt)
    assert isinstance(parsed.confidence, dict)
    assert parsed.confidence_level in VALID_LEVELS
