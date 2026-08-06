"""Pre-implementation interface + behavioral tests for the AI Scan feature.

Covers the frontend side of the LLM-vision OCR feature (parent task
t_44105a69, acceptance criteria #6): the "AI Scan" toggle in the upload
flow, the result panel showing AI-extracted fields with confidence, the
source marker (vision vs tesseract), the friendly Tesseract-fallback
notice, and the empty-state UX.

API contract (from the original acceptance criteria): the AI-mode upload
response contains a `source` field ("vision" | "tesseract") and, when AI
mode is enabled, `ai_result` and `tesseract_result` payloads carrying the
same receipt/confidence shape as the Tesseract path. The frontend may
develop against mocked data until the backend lands.

Layout (mirrors tests/test_frontend.py):
  * Interface tests — filesystem / type / API-contract checks that must
    pass once the scaffolding files exist.
  * Behavioral tests — acceptance-criteria assertions on the UI pieces.

Run with:
    .venv/bin/python -m pytest tests/test_frontend_ai_scan.py -v
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FRONTEND = REPO_ROOT / "frontend"


def _read_ts(relpath: str) -> str:
    """Read a TypeScript file from frontend/ and return its content."""
    path = FRONTEND / relpath
    if not path.exists():
        pytest.fail(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def _ts_has_interface(content: str, name: str) -> bool:
    pattern = rf"export\s+(interface|type)\s+{re.escape(name)}\b"
    return bool(re.search(pattern, content))


def _ts_has_function(content: str, name: str) -> bool:
    pattern = rf"export\s+(async\s+)?function\s+{re.escape(name)}\b"
    return bool(re.search(pattern, content))


def _ts_has_export_const(content: str, name: str) -> bool:
    pattern = rf"export\s+const\s+{re.escape(name)}\s*=\s*(async\s+)?\("
    return bool(re.search(pattern, content))


def _ts_has_component(content: str, name: str) -> bool:
    pattern = rf"export\s+(default\s+)?(function|const)\s+{re.escape(name)}\b"
    return bool(re.search(pattern, content))


# ============================================================================
# INTERFACE TESTS — API contract scaffolding
# ============================================================================


class TestAiScanTypes:
    """lib/types.ts defines the AI-mode OCR contract types."""

    @pytest.fixture(scope="class")
    def types_content(self) -> str:
        return _read_ts("lib/types.ts")

    def test_ocr_source_type_exists(self, types_content: str) -> None:
        assert _ts_has_interface(types_content, "OcrSource") or "OcrSource" in types_content, (
            "lib/types.ts must define OcrSource ('vision' | 'tesseract')"
        )

    def test_ocr_source_has_vision_and_tesseract(self, types_content: str) -> None:
        assert "vision" in types_content and "tesseract" in types_content, (
            "OcrSource must include both 'vision' and 'tesseract'"
        )

    def test_ai_extraction_type_exists(self, types_content: str) -> None:
        assert _ts_has_interface(types_content, "AiExtraction"), (
            "lib/types.ts must define AiExtraction (the ai_result/tesseract_result payload)"
        )

    def test_ai_extraction_has_confidence(self, types_content: str) -> None:
        content = _read_ts("lib/types.ts")
        assert "confidence" in content, "AiExtraction must carry per-field confidence"

    def test_ai_scan_response_type_exists(self, types_content: str) -> None:
        assert _ts_has_interface(types_content, "AiScanUploadResponse"), (
            "lib/types.ts must define AiScanUploadResponse for the AI-mode upload"
        )

    def test_ai_scan_response_has_source(self, types_content: str) -> None:
        assert "source" in types_content, (
            "AiScanUploadResponse must include the 'source' field"
        )

    def test_ai_scan_response_has_ai_and_tesseract_results(self, types_content: str) -> None:
        assert "ai_result" in types_content and "tesseract_result" in types_content, (
            "AiScanUploadResponse must expose ai_result and tesseract_result"
        )


class TestAiScanApiClient:
    """lib/api.ts exports an AI-mode upload function."""

    @pytest.fixture(scope="class")
    def api_content(self) -> str:
        return _read_ts("lib/api.ts")

    def test_upload_receipt_with_ai_exists(self, api_content: str) -> None:
        assert _ts_has_function(api_content, "uploadReceiptWithAi") or _ts_has_export_const(
            api_content, "uploadReceiptWithAi"
        ), "lib/api.ts must export uploadReceiptWithAi()"

    def test_upload_with_progress_accepts_extra_form_fields(self, api_content: str) -> None:
        assert "formFields" in api_content or "extra" in api_content, (
            "uploadWithProgress must accept extra FormData fields (e.g. ai_scan=true)"
        )

    def test_ai_mode_posts_ai_scan_flag(self, api_content: str) -> None:
        assert "ai_scan" in api_content, (
            "AI-mode upload must post an 'ai_scan' form field to the backend"
        )


class TestAiScanMock:
    """lib/aiScanMock.ts provides dev-mode data following the API contract."""

    def test_mock_module_exists(self) -> None:
        path = FRONTEND / "lib/aiScanMock.ts"
        assert path.exists(), "lib/aiScanMock.ts must exist (dev mock until backend lands)"

    def test_mock_has_vision_response(self) -> None:
        content = _read_ts("lib/aiScanMock.ts")
        assert "vision" in content.lower(), "Mock must include a vision-source response"

    def test_mock_has_tesseract_fallback_response(self) -> None:
        content = _read_ts("lib/aiScanMock.ts")
        assert "tesseract" in content.lower(), (
            "Mock must include a Tesseract fallback response with a source marker"
        )


# ============================================================================
# INTERFACE TESTS — UI components
# ============================================================================


class TestAiScanToggle:
    """components/AiScanToggle.tsx is an accessible switch."""

    def test_toggle_component_exists(self) -> None:
        path = FRONTEND / "components/AiScanToggle.tsx"
        assert path.exists(), "components/AiScanToggle.tsx must exist"

    def test_toggle_component_exports(self) -> None:
        content = _read_ts("components/AiScanToggle.tsx")
        assert _ts_has_component(content, "AiScanToggle"), (
            "AiScanToggle.tsx must export an AiScanToggle component"
        )

    def test_toggle_uses_switch_semantics(self) -> None:
        content = _read_ts("components/AiScanToggle.tsx")
        assert "role=\"switch\"" in content, "Toggle must use role=\"switch\" semantics"
        assert "aria-checked" in content, "Toggle must expose aria-checked state"

    def test_toggle_is_controllable(self) -> None:
        content = _read_ts("components/AiScanToggle.tsx")
        assert "checked" in content and "onChange" in content, (
            "Toggle must accept checked + onChange props"
        )

    def test_toggle_mentions_ai_scan(self) -> None:
        content = _read_ts("components/AiScanToggle.tsx")
        assert "AI Scan" in content, "Toggle must be labeled 'AI Scan'"


class TestAiResultPanel:
    """components/AiResultPanel.tsx renders source, confidence, fallback."""

    def test_panel_component_exists(self) -> None:
        path = FRONTEND / "components/AiResultPanel.tsx"
        assert path.exists(), "components/AiResultPanel.tsx must exist"

    def test_panel_component_exports(self) -> None:
        content = _read_ts("components/AiResultPanel.tsx")
        assert _ts_has_component(content, "AiResultPanel"), (
            "AiResultPanel.tsx must export an AiResultPanel component"
        )

    def test_panel_renders_source(self) -> None:
        content = _read_ts("components/AiResultPanel.tsx")
        assert "source" in content, "Panel must render the extraction source"

    def test_panel_renders_confidence(self) -> None:
        content = _read_ts("components/AiResultPanel.tsx")
        assert "confidence" in content or "ConfidenceBadge" in content, (
            "Panel must show per-field confidence"
        )

    def test_panel_has_fallback_notice(self) -> None:
        content = _read_ts("components/AiResultPanel.tsx")
        assert "fallback" in content.lower() or "tesseract" in content.lower(), (
            "Panel must include a friendly fallback notice when Tesseract was used"
        )

    def test_panel_shows_merchant_date_total(self) -> None:
        content = _read_ts("components/AiResultPanel.tsx")
        for term in ["merchant", "vendor", "date", "total"]:
            assert term in content.lower(), (
                f"Panel must display the '{term}' field"
            )


class TestUploadPageIntegration:
    """Upload page wires toggle + result panel + empty state."""

    @pytest.fixture(scope="class")
    def upload_content(self) -> str:
        return _read_ts("app/(app)/upload/page.tsx")

    def test_upload_uses_ai_scan_toggle(self, upload_content: str) -> None:
        assert "AiScanToggle" in upload_content, (
            "Upload page must render the AiScanToggle component"
        )

    def test_upload_uses_ai_result_panel(self, upload_content: str) -> None:
        assert "AiResultPanel" in upload_content, (
            "Upload page must render the AiResultPanel component"
        )

    def test_upload_has_empty_state(self, upload_content: str) -> None:
        assert "EmptyState" in upload_content, (
            "Upload page must keep an empty-state UX"
        )

    def test_upload_passes_ai_flag_to_hook(self, upload_content: str) -> None:
        assert "aiScan" in upload_content, (
            "Upload page must pass the AI Scan flag into the upload flow"
        )


class TestUseUploadHook:
    """useUpload supports AI-mode uploads."""

    @pytest.fixture(scope="class")
    def hook_content(self) -> str:
        return _read_ts("lib/hooks/useUpload.ts")

    def test_hook_accepts_ai_scan(self, hook_content: str) -> None:
        assert "aiScan" in hook_content, (
            "useUpload must accept an AI Scan flag per upload"
        )

    def test_hook_exposes_ai_result(self, hook_content: str) -> None:
        assert "aiResult" in hook_content or "source" in hook_content, (
            "useUpload must expose the AI-mode result (source + ai_result)"
        )

    def test_hook_selects_ai_api(self, hook_content: str) -> None:
        assert "uploadReceiptWithAi" in hook_content, (
            "useUpload must call uploadReceiptWithAi when AI Scan is enabled"
        )
