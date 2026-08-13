"""
BDD regression contract for F1.5 — the consumer 3-step onboarding flow
(docs/plans/consumer-pivot-2026-08-13.md, §4 / F1.5).

Scope: frontend contract tests. The flow lives in the Next.js frontend
(app/onboarding/page.tsx + components/Onboarding.tsx), so this module
asserts the source-of-truth artifacts that encode the acceptance criteria:

  1. The onboarding consists of exactly 3 steps, with a sticky progress
     indicator and forward/back navigation, and is always skippable.
  2. Step 1 shows the one-sentence positioning promise (§3.1):
     "Fotózd le a nyugtát. Mi megmutatjuk, hol folyik el a pénzed — és hol
     takaríthatsz meg."
  3. Finishing navigates to the consumer dashboard (/dashboard).
  4. State persistence: preferences.onboarding_done gates the flow — a user
     who already completed onboarding is not shown it again.
  5. Step 2 offers camera / upload access (capture input or camera button).

Backend wire format is untouched by this feature (schema change is F1.3).
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"

# Plan §3.1 — the one-sentence positioning promise. Must appear verbatim in
# the step-1 copy of BOTH surfaces (dedicated page and shell modal).
PROMISE = (
    "Fotózd le a nyugtát. Mi megmutatjuk, hol folyik el a pénzed"
    " — és hol takaríthatsz meg."
)

# Acceptance 3 — the post-onboarding destination.
DASHBOARD_HREF = "/dashboard"


def _read(rel: str) -> str:
    path = FRONTEND / rel
    assert path.exists(), f"{rel} missing — F1.5 onboarding contract depends on it"
    return path.read_text(encoding="utf-8")


def test_f15_onboarding_page_exists() -> None:
    """The dedicated onboarding route exists (app/onboarding/page.tsx)."""
    assert (FRONTEND / "app/onboarding/page.tsx").exists()


def test_f15_exactly_three_steps() -> None:
    """Acceptance 1: the flow is 3 steps — value promise, camera/upload,
    first receipt — with a sticky indicator and forward/back navigation."""
    page = _read("app/onboarding/page.tsx")
    modal = _read("components/Onboarding.tsx")

    for src, label in ((page, "onboarding page"), (modal, "onboarding modal")):
        # Exactly three step definitions (icon/title/body tuples).
        assert "title: \"Mi ez?\"" in src, f"{label}: step 1 (Mi ez?) missing"
        assert "title: \"Kamera hozzáférése\"" in src, f"{label}: step 2 (camera access) missing"
        assert "title: \"Az első nyugtád\"" in src, f"{label}: step 3 (first receipt) missing"

        # Sticky progress indicator (back/forward state preserved across steps).
        assert re.search(r"aria-label=.*lépés", src), f"{label}: step counter missing"
        assert "setStep((value) => value - 1)" in src, f"{label}: Back navigation missing"
        assert "setStep((value) => value + 1)" in src, f"{label}: Next navigation missing"


def test_f15_step1_shows_positioning_promise() -> None:
    """Acceptance 2: step 1 shows the one-sentence positioning promise (§3.1)."""
    page = _read("app/onboarding/page.tsx")
    modal = _read("components/Onboarding.tsx")

    assert PROMISE in page, (
        "onboarding page step 1 must show the positioning promise verbatim"
    )
    assert PROMISE in modal, (
        "onboarding modal step 1 must show the positioning promise verbatim"
    )


def test_f15_finish_navigates_to_consumer_dashboard() -> None:
    """Acceptance 3: after the flow, the user lands on /dashboard."""
    page = _read("app/onboarding/page.tsx")
    modal = _read("components/Onboarding.tsx")

    assert f'router.push("{DASHBOARD_HREF}")' in page, (
        "onboarding page must navigate to /dashboard on finish"
    )
    assert f'router.push("{DASHBOARD_HREF}")' in modal, (
        "onboarding modal must navigate to /dashboard on finish"
    )


def test_f15_state_persistence_prevents_replay() -> None:
    """Acceptance 4: onboarding_done gates the flow — completed users never
    see it again (persistence is the preferences API)."""
    page = _read("app/onboarding/page.tsx")
    modal = _read("components/Onboarding.tsx")

    # Both surfaces must persist completion through the preferences API.
    assert "savePreferences({ onboarding_done: true })" in page, (
        "onboarding page must persist onboarding_done via savePreferences"
    )
    assert "savePreferences({ onboarding_done: true })" in modal, (
        "onboarding modal must persist onboarding_done via savePreferences"
    )
    # The modal must not render for users who already completed onboarding.
    assert "onboarding_done" in modal and "getPreferences" in modal, (
        "onboarding modal must gate on preferences.onboarding_done"
    )
    # The dedicated page must redirect already-onboarded users to the
    # dashboard instead of replaying the flow.
    assert "getPreferences" in page and 'router.replace("/dashboard")' in page, (
        "onboarding page must redirect completed users to the dashboard"
    )


def test_f15_step2_offers_camera_and_upload_access() -> None:
    """Acceptance (step 2): camera capture + gallery upload access for the
    first receipt. The dedicated page owns the picker (camera capture input
    with a visible camera button and a gallery fallback)."""
    page = _read("app/onboarding/page.tsx")

    assert "capture=\"environment\"" in page, (
        "onboarding page must offer camera capture via <input capture>"
    )
    assert "Fénykép készítése" in page, (
        "onboarding page must surface a camera button on step 2"
    )
    assert "Feltöltés az eszközről" in page, (
        "onboarding page must offer gallery upload on step 2"
    )


def test_f15_step3_shows_first_receipt_result() -> None:
    """Acceptance (step 3): the first receipt is submitted and the extracted
    result is presented (vendor + total + confidence) before navigating on."""
    page = _read("app/onboarding/page.tsx")

    assert "uploadReceipt" in page, (
        "step 3 must submit the first receipt through the real upload API"
    )
    assert "Feldolgozás…" in page, (
        "step 3 must show an in-flight processing state"
    )
    assert "vendor" in page and "total" in page, (
        "step 3 must render the extracted vendor and total"
    )
