#!/usr/bin/env python3
"""Measure VERITAS structured test-metadata coverage across the whole test suite.

The numbers in ``.ai/project-profile.yaml`` (``traceability_measurement``) and in
``.ai/quality-gates.yaml`` (gate 10 ``measured``) come from this script. Run it
to re-measure instead of trusting a hand-copied figure:

    python scripts/count_traceability_coverage.py            # human report
    python scripts/count_traceability_coverage.py --json     # machine readable

WHY THIS EXISTS
---------------
``verify_test_metadata()`` in ``scripts/veritas_gate.py`` is delta-scoped: it
inspects only test files present in the git diff and returns ``True`` early
when the diff touches none (L447-449). It therefore cannot observe the 82
test files that predate the policy. This script is the repo-wide measurement
that makes that blindness visible.

SCOPE AND LIMITS (read before quoting a number)
-----------------------------------------------
The classification below mirrors ``verify_test_metadata()`` deliberately, so
the two agree on what "compliant" means:

  * a marker counts only when called with a non-empty string literal
    (a bare ``@pytest.mark.test_id`` carries no traceability);
  * only the contiguous ``@`` decorator block immediately above ``def test_*``
    is considered.

It is a static, textual measurement. It cannot tell whether a marker points at
a requirement that actually exists, and it does not resolve parameterized
tests. It answers exactly one question: how many test functions carry all
three mandatory markers.

COMMITTED TREE ONLY (default)
------------------------------
By default the measurement reads a **committed** tree via ``git ls-tree`` /
``git show``, not the working tree and not the index. The figure therefore
describes a committed state and is reproducible by anyone who checks out the
same commit.

This matters more than it looks. In a shared workspace the git *index* can
contain files that are staged but uncommitted by a concurrent agent, so an
index-based count silently includes another run's in-flight work. A figure
pinned in ``.ai/project-profile.yaml`` must not move because someone else is
mid-write. Files present only in the working tree are counted separately and
labelled, never folded into the headline number.

``--ref`` selects which commit to measure (default ``HEAD``). A figure
recorded for a specific commit must be re-checkable after HEAD has moved on,
so ``--ref <recorded-commit>`` reproduces the original measurement exactly.
``--include-worktree`` measures the raw working tree instead.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = REPO_ROOT / "tests"

# Must stay in sync with REQUIRED_TEST_MARKERS in scripts/veritas_gate.py.
REQUIRED_TEST_MARKERS = ("test_id", "requirements", "scenario")

_MARKER_PATTERNS = {
    name: re.compile(rf"pytest\.mark\.{re.escape(name)}\(\s*[\"'][^\"']+[\"']\s*[,)]")
    for name in REQUIRED_TEST_MARKERS
}

_TEST_DEF = re.compile(r"\s*(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)")


def _decorator_block(lines: list[str], def_index: int) -> str:
    """Return the contiguous '@' decorator lines directly above ``def_index``."""
    decorators: list[str] = []
    cursor = def_index - 1
    while cursor >= 0 and lines[cursor].lstrip().startswith("@"):
        decorators.append(lines[cursor].strip())
        cursor -= 1
    return "\n".join(decorators)


def missing_markers(block: str) -> list[str]:
    return [name for name, pattern in _MARKER_PATTERNS.items() if not pattern.search(block)]


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _discover(ref: str, include_worktree: bool) -> tuple[dict[str, str], list[str]]:
    """Return ({relpath: source text}, work-tree-only files).

    Default reads a committed tree so the result is reproducible from a
    commit alone. ``include_worktree`` reads files off disk instead.
    """
    if include_worktree:
        sources = {
            p.relative_to(REPO_ROOT).as_posix(): p.read_text(encoding="utf-8-sig", errors="strict")
            for p in TEST_ROOT.rglob("test_*.py")
        }
        return sources, []

    try:
        names = [
            line
            for line in _git("ls-tree", "-r", "--name-only", ref, "--", "tests/").split()
            if line.endswith(".py") and line.rsplit("/", 1)[-1].startswith("test_")
        ]
        sources = {name: _git("show", f"{ref}:{name}") for name in names}
    except (OSError, RuntimeError) as exc:
        print(f"[WARN] Cannot read {ref} ({exc}); falling back to the working tree.", file=sys.stderr)
        return _discover(ref, include_worktree=True)

    on_disk = {p.relative_to(REPO_ROOT).as_posix() for p in TEST_ROOT.rglob("test_*.py")}
    return sources, sorted(on_disk - set(sources))


def measure(ref: str = "HEAD", include_worktree: bool = False) -> dict:
    sources, worktree_only = _discover(ref, include_worktree)
    total = compliant = 0
    noncompliant_files: list[dict] = []

    for rel in sorted(sources):
        lines = sources[rel].lstrip("﻿").splitlines()
        file_missing = 0
        for index, line in enumerate(lines):
            if not _TEST_DEF.match(line):
                continue
            total += 1
            if missing_markers(_decorator_block(lines, index)):
                file_missing += 1
            else:
                compliant += 1
        if file_missing:
            noncompliant_files.append({"file": rel, "missing": file_missing})

    return {
        "scope": "working_tree" if include_worktree else "committed_tree",
        "ref": ref if not include_worktree else "working_tree",
        "test_files_total": len(sources),
        "test_functions_total": total,
        "functions_with_all_three_markers": compliant,
        "functions_missing_markers": total - compliant,
        "compliant_percent": round(100 * compliant / total, 1) if total else 0.0,
        "files_with_at_least_one_noncompliant_test": len(noncompliant_files),
        "files_fully_compliant": len(sources) - len(noncompliant_files),
        "enforcement_scope": "delta_only",
        "worktree_only_files_excluded": worktree_only,
        "noncompliant_files": noncompliant_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--list-files", action="store_true", help="list every non-compliant file path"
    )
    parser.add_argument(
        "--ref",
        default="HEAD",
        help="commit to measure (default: HEAD). Use the commit a figure was "
        "recorded at to reproduce it after HEAD has moved on.",
    )
    parser.add_argument(
        "--include-worktree",
        action="store_true",
        help="measure the working tree instead of a committed tree (default)",
    )
    args = parser.parse_args()

    if not TEST_ROOT.is_dir() and not args.include_worktree:
        print(f"[FAIL] No test directory at {TEST_ROOT}", file=sys.stderr)
        return 2

    report = measure(ref=args.ref, include_worktree=args.include_worktree)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    print("VERITAS structured test-metadata coverage")
    print(f"  scope:                            {report['scope']} @ {report['ref']}")
    print(f"  test files:                       {report['test_files_total']}")
    print(f"  test functions:                   {report['test_functions_total']}")
    print(
        f"  with all three markers:           "
        f"{report['functions_with_all_three_markers']} "
        f"({report['compliant_percent']}%)"
    )
    print(f"  missing at least one marker:      {report['functions_missing_markers']}")
    print(
        f"  files with >=1 non-compliant test:{report['files_with_at_least_one_noncompliant_test']}"
        f"  (fully compliant: {report['files_fully_compliant']})"
    )
    print(f"  enforcement scope:                {report['enforcement_scope']}")

    if report["worktree_only_files_excluded"]:
        print("  work-tree-only files excluded (not in the committed tree):")
        for path in report["worktree_only_files_excluded"]:
            print(f"    {path}")

    if args.list_files:
        for entry in report["noncompliant_files"]:
            print(f"    {entry['file']}  ({entry['missing']})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
