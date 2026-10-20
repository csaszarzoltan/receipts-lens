"""The OCR bake-off scores fields right or wrong, not characters (I14)."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location(
    "ocr_bakeoff", Path(__file__).parent.parent / "scripts" / "ocr_bakeoff.py")
bakeoff = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bakeoff)


def test_field_correct_rules():
    assert bakeoff.field_correct("total", 19.5, 19.50)
    assert not bakeoff.field_correct("total", 19.5, 2026.0)
    assert not bakeoff.field_correct("total", 19.5, None)
    assert bakeoff.field_correct("vendor", "COOP SUPERMARKT", "Coop Supermarkt J")
    assert bakeoff.field_correct("date", "2026-08-13", "2026-08-13")
    assert not bakeoff.field_correct("date", "2026-08-13", "2026-08-31")


def test_score_counts_each_field_and_skips_missing_images(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    labels = {"a.jpg": {"vendor": "COOP", "date": "2026-08-13", "total": 19.5},
              "missing.jpg": {"vendor": "X", "date": "2026-01-01", "total": 1.0}}
    parse = lambda data: SimpleNamespace(total=2026.0, date="2026-08-13", merchant="COOP SUPERMARKT J")
    result = bakeoff.score(labels, tmp_path, parse)
    assert result["files"] == 1
    assert result["accuracy"] == {"total": 0.0, "date": 1.0, "vendor": 1.0}
