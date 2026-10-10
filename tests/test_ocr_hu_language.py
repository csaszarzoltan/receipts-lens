"""Hungarian OCR language: "hun" is supported only when Tesseract has it.

Falls back to "eng" (never fails the request) when the trained data is absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app import ocr

DOCKERFILE = Path(__file__).resolve().parent.parent / "infra" / "Dockerfile"


@pytest.mark.test_id("TEST-RL-V02-165")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_hun_is_a_supported_language():
    assert "hun" in ocr.SUPPORTED_LANGUAGES


@pytest.mark.test_id("TEST-RL-V02-166")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_hun_falls_back_to_eng_when_pack_not_installed(monkeypatch):
    monkeypatch.setattr(ocr, "_installed_languages", lambda: {"eng", "osd"})
    assert ocr.resolve_ocr_language("hun") == "eng"


@pytest.mark.test_id("TEST-RL-V02-167")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_hun_is_used_when_pack_installed(monkeypatch):
    monkeypatch.setattr(ocr, "_installed_languages", lambda: {"eng", "hun"})
    assert ocr.resolve_ocr_language("hun") == "hun"


@pytest.mark.parametrize("installed", [set(), {"osd"}, {"eng", "hun"}])
@pytest.mark.test_id("TEST-RL-V02-168")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_eng_is_returned_whatever_is_installed(monkeypatch, installed):
    monkeypatch.setattr(ocr, "_installed_languages", lambda: installed)
    assert ocr.resolve_ocr_language("eng") == "eng"


@pytest.mark.test_id("TEST-RL-V02-169")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_dockerfile_installs_hungarian_trained_data():
    # Package lines in the apt list end with a " \" line continuation.
    packages = [
        line.strip().rstrip("\\").strip()
        for line in DOCKERFILE.read_text(encoding="utf-8").splitlines()
    ]
    assert "tesseract-ocr-hun" in packages


@pytest.mark.test_id("TEST-RL-V02-170")
@pytest.mark.requirements("FEAT-RL-V02-REQ-059")
@pytest.mark.scenario("AC-RL-V02-40")
def test_extract_text_falls_back_to_eng_when_hun_pack_missing(monkeypatch):
    """A request for Hungarian must not fail when the pack is not installed."""
    from app import ocr

    seen = {}

    def fake_image_to_string(image, lang, config):
        seen["lang"] = lang
        return "text"

    monkeypatch.setattr(ocr, "_installed_languages", lambda: frozenset({"eng", "osd"}))
    monkeypatch.setattr(ocr, "preprocess_image", lambda b: b)
    monkeypatch.setattr(ocr.pytesseract, "image_to_string", fake_image_to_string)
    assert ocr.extract_text(b"img", lang="hun") == "text"
    assert seen["lang"] == "eng"
