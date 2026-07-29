"""Documentation contract for the tested Windows quickstart."""
from pathlib import Path


def test_windows_guide_contains_reproducible_commands() -> None:
    text = Path("docs/WINDOWS_GUIDE_HU.md").read_text(encoding="utf-8")
    for expected in (
        "py -3.11 -m venv .venv",
        'python -m pip install -e ".[dev]"',
        'python -m uvicorn app.main:app',
        "python -m pytest -ra",
        "tesseract --version",
        "curl.exe",
    ):
        assert expected in text
