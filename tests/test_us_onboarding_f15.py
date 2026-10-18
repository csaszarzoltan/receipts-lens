"""F1.5 onboarding contract, superseded by the approved REQ-UX-10/18 flow.

The 2026-10-12 plan replaces the three introductory slides with an immediate
receipt workflow. Save, error, picker and camera behavior is tested by the
frontend regression runner; this bridge runs those behaviors from pytest too.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


@pytest.fixture(scope="module")
def onboarding_behaviors():
    node = shutil.which("node")
    if not node or not (FRONTEND / "node_modules/typescript").is_dir():
        pytest.skip("Frontend dependencies and Node are required for behavioral checks")
    result = subprocess.run([node, str(FRONTEND / "tests/ux-regressions.cjs")],
                            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


@pytest.mark.requirements("REQ-UX-10")
def test_onboarding_page_and_modal_use_same_receipt_flow():
    for relative in ("app/onboarding/page.tsx", "components/Onboarding.tsx"):
        source = (FRONTEND / relative).read_text()
        assert "<OnboardingFlow" in source


@pytest.mark.requirements("REQ-UX-10")
def test_onboarding_saves_currency_and_preserves_page_on_save_failure(onboarding_behaviors):
    assert re.search(r"^ok \d+ - REQ-UX-10 .*shared onboarding saves currency",
                     onboarding_behaviors, re.MULTILINE)


@pytest.mark.requirements("REQ-UX-01", "REQ-UX-18")
def test_first_receipt_picker_and_camera_behaviors(onboarding_behaviors):
    for behavior in ("file chooser is a real working button",
                     "camera double activation makes only one media request",
                     "cancelled camera request never opens and releases late stream",
                     "capture waits for preview and emits only one JPEG",
                     "failed image encoding keeps camera open and allows retry"):
        assert re.search(r"^ok \d+ - .*" + re.escape(behavior),
                         onboarding_behaviors, re.MULTILINE)
