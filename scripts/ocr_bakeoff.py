#!/usr/bin/env python3
"""Field-level OCR accuracy on hand-labelled receipts (total, date, vendor).

Character error rate hides a misread total; this scores each field as right or
wrong, so an OCR engine change can be judged on the fields users confirm.

Usage: python scripts/ocr_bakeoff.py [--images DIR] [--labels FILE] [--min-total ACC]
Exit code 1 when the total accuracy is below --min-total (default 0, report only).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIELDS = ("total", "date", "vendor")


def _norm(text: str | None) -> str:
    return re.sub(r"\W+", "", (text or "").lower())


def field_correct(field: str, expected, got) -> bool:
    """True when the OCR value for ``field`` matches the label."""
    if got is None:
        return False
    if field == "total":
        return round(float(got), 2) == round(float(expected), 2)
    if field == "vendor":
        a, b = _norm(expected), _norm(got)
        return bool(a and b and (a in b or b in a))
    return str(got) == str(expected)


def score(labels: dict, images: Path, parse) -> dict:
    """Per-file results and per-field accuracy for every labelled image present in ``images``."""
    rows, hits, seen = [], {f: 0 for f in FIELDS}, 0
    for name, expected in sorted(labels.items()):
        path = images / name
        if not path.exists():
            continue
        parsed = parse(path.read_bytes())
        got = {"total": parsed.total, "date": parsed.date, "vendor": parsed.merchant}
        ok = {f: field_correct(f, expected[f], got[f]) for f in FIELDS}
        seen += 1
        for f in FIELDS:
            hits[f] += int(ok[f])
        rows.append({"file": name, "expected": expected, "got": got, "correct": ok})
    return {"files": seen, "rows": rows,
            "accuracy": {f: (hits[f] / seen if seen else None) for f in FIELDS}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--images", type=Path, default=ROOT / "frontend/e2e/fixtures")
    parser.add_argument("--labels", type=Path, default=ROOT / "tests/ocr_labels/labels.json")
    parser.add_argument("--min-total", type=float, default=0.0)
    args = parser.parse_args()

    from app.ocr import parse_receipt_with_confidence

    result = score(json.loads(args.labels.read_text()), args.images, parse_receipt_with_confidence)
    for row in result["rows"]:
        marks = " ".join(f"{f}={'ok' if row['correct'][f] else 'WRONG'}" for f in FIELDS)
        print(f"{row['file']}: {marks}  got={row['got']}")
    print("accuracy", json.dumps(result["accuracy"]), "files", result["files"])
    if not result["files"]:
        print("no labelled images found", file=sys.stderr)
        return 2
    return 0 if result["accuracy"]["total"] >= args.min_total else 1


if __name__ == "__main__":
    raise SystemExit(main())
