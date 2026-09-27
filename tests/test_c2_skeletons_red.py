"""RED tests for C2 skeletons (AC1-2) — expect loading.tsx, FAIL before impl.

Target Files: frontend/app/(app)/upload/loading.tsx, frontend/app/(app)/receipts/loading.tsx
AC1: skeletons exist, export default Loading, import from @/components/Skeleton, no "use client"
AC2: layout FOUC guard intact + loading files exist + no Suspense + file-disjoint with C3
"""
from __future__ import annotations

import pathlib
import subprocess

ROOT = pathlib.Path(__file__).parent.parent
UPLOAD_LOADING = ROOT / "frontend" / "app" / "(app)" / "upload" / "loading.tsx"
RECEIPTS_LOADING = ROOT / "frontend" / "app" / "(app)" / "receipts" / "loading.tsx"
LAYOUT = ROOT / "frontend" / "app" / "layout.tsx"
C3_ALLOWLIST = [
    ROOT / "app" / "preprocessing.py",
    ROOT / "app" / "ocr.py",
    ROOT / "frontend" / "components" / "ConfidenceBadge.tsx",
]


def test_ac1_loading_skeletons_exist():
    """AC1 — both loading.tsx must exist, export default Loading, import Skeleton primitives."""
    assert UPLOAD_LOADING.exists(), f"AC1 RED: missing {UPLOAD_LOADING} — C2 not implemented yet"
    assert RECEIPTS_LOADING.exists(), f"AC1 RED: missing {RECEIPTS_LOADING} — C2 not implemented yet"

    for path, expected_import in [
        (UPLOAD_LOADING, "PageSkeleton"),
        (RECEIPTS_LOADING, "SkeletonCard"),
    ]:
        text = path.read_text(encoding="utf-8")
        assert "export default function Loading" in text, f"AC1 RED: {path.name} missing 'export default function Loading'"
        assert "@/components/Skeleton" in text, f"AC1 RED: {path.name} missing import from '@/components/Skeleton'"
        assert expected_import in text, f"AC1 RED: {path.name} should import {expected_import}"
        assert '"use client"' not in text and "'use client'" not in text, f"AC1 RED: {path.name} must not contain 'use client' (server component)"


def test_ac2_no_layout_break_and_disjoint():
    """AC2 — layout FOUC guard intact + loading files present + no Suspense + C3 file-disjoint.

    RED before impl: fails because loading.tsx files are absent.
    GREEN after impl: layout guard intact, loading files have no Suspense/client hooks,
    and git diff touches only the two loading.tsx (no C3 overlap).
    """
    # FOUC guard intact — layout.tsx must still inject theme/locale scripts
    assert LAYOUT.exists(), f"AC2 RED: missing {LAYOUT}"
    layout_text = LAYOUT.read_text(encoding="utf-8")
    assert "THEME_INIT_SCRIPT" in layout_text, "AC2 RED: THEME_INIT_SCRIPT missing from layout.tsx (FOUC guard)"
    assert "LOCALE_INIT_SCRIPT" in layout_text, "AC2 RED: LOCALE_INIT_SCRIPT missing from layout.tsx"

    # RED gate — both loading files must exist; fails now, passes after GREEN
    assert UPLOAD_LOADING.exists(), f"AC2 RED: missing {UPLOAD_LOADING} — C2 not implemented yet"
    assert RECEIPTS_LOADING.exists(), f"AC2 RED: missing {RECEIPTS_LOADING} — C2 not implemented yet"

    # Negative guards (checked once files exist)
    for path in [UPLOAD_LOADING, RECEIPTS_LOADING]:
        text = path.read_text(encoding="utf-8")
        assert "Suspense" not in text, f"AC2 RED: {path.name} must not contain <Suspense> (double-wrap guard)"
        assert "useSearchParams" not in text, f"AC2 RED: {path.name} must not import useSearchParams"
        assert "useSWR" not in text and "swr" not in text.lower().split("skeleton")[0], f"AC2 RED: {path.name} must not import useSWR"

    # File-disjoint with C3 — C2 diff must not touch C3 allowlist
    # Check git diff --name-only against C3 allowlist (untracked docs/plans excluded)
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    changed = set(result.stdout.splitlines())
    # Also include staged changes
    result2 = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    changed |= set(result2.stdout.splitlines())
    for c3_path in C3_ALLOWLIST:
        rel = str(c3_path.relative_to(ROOT))
        assert rel not in changed, f"AC2 RED: C3 file {rel} must not be in C2 diff (file-disjoint)"
