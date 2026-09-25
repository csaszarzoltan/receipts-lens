#!/usr/bin/env python3
"""Traceability runner — writes the artifact gate 10 verifies (ZOO-21).

Gate 10's ``require_runner_generated_traceability`` was, until this script
existed, UNSATISFIABLE: nothing in the repo emitted a traceability artifact, so
there was nothing for a gate to read. This is that runner. It produces a
deterministic, re-runnable artifact and the gate consumes it.

WHAT IT WRITES
--------------
``.agent-pipeline/audit/traceability.json`` — a machine-readable
spec -> test traceability report. Written to a path that is ALREADY tracked
(``.agent-pipeline/audit/`` holds the gate's own jsonl audit log), so the
artifact can be committed, diffed, and reviewed like any other source file.
That matters: a runner whose output is only ever printed to a log is not
evidence, because nobody can review what changed.

THE THREE CHECKS, AND WHY THEY DIFFER BY MARKER
------------------------------------------------
The three markers are not the same kind of thing, so they are not checked the
same way. Treating them uniformly is the most obvious way to build a dishonest
gate, so it is worth being explicit:

  * ``requirements(...)`` and ``scenario(...)`` name something OUTSIDE the test
    suite — a spec requirement or an acceptance scenario. They are resolved
    against the real spec corpus. A marker pointing at a requirement that does
    not exist is a false traceability claim, and marker-presence counting
    cannot see it.
  * ``test_id(...)`` names the test ITSELF. It is not a spec reference, so
    resolving it against specs would be a category error that manufactures
    false failures. Its traceability property is IDENTITY, not resolution: a
    test id must be unique across the suite, or "look this test up by its id"
    stops being well-defined.

It also scans ``.agent-pipeline/03_e2e_suites/`` as well as ``tests/``.
``verify_test_metadata()`` has always scanned both; the coverage counter only
ever looked at ``tests/``, so its 416 e2e test functions were structurally
invisible to the only repo-wide measurement in the repo.

It deliberately imports the classifier from the coverage counter rather than
re-implementing it, so "compliant" cannot mean two different things in one repo.

DETERMINISM
-----------
Like the coverage counter, the default run reads a COMMITTED tree (``HEAD``)
via ``git ls-tree``/``git show``, never the working tree and never the index. In
a shared workspace the index can hold another agent's staged-but-uncommitted
files; a figure pinned into ``.ai/`` must not move because someone else is
mid-write. ``--include-worktree`` measures the working tree instead.

The artifact records the commit it was generated from, so a reader can tell
exactly which tree a report describes and re-generate it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from count_traceability_coverage import (  # noqa: E402  (path setup must precede import)
    _TEST_DEF,
    _decorator_block,
    measure as measure_coverage,
    missing_markers,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / ".agent-pipeline" / "audit" / "traceability.json"

# The test trees the gate actually enforces on (see verify_test_metadata()).
# The e2e suite is included because verify_test_metadata() has always scanned
# it; excluding it here would understate the gap the gate can actually see.
TEST_TREES = ("tests", ".agent-pipeline/03_e2e_suites")

# Spec corpus, as regexes over the repo-relative path. Index every corpus; a
# reference resolves if it appears in ANY of them, because the repo carries
# spec families in several places and a marker naming a FEAT-* id is not invalid
# just because that id lives in .agent-pipeline/ rather than docs/specs/.
SPEC_PATH_PATTERNS = (
    r"\.agent-pipeline/02_specs/.*\.md",
    r"docs/specs/.*\.md",
    r"specs/.*\.md",
)

# REQ-047-01, FEAT-RL-V02-REQ-020, AC-RL-V02-20, SPEC-038, TEST-RL-V02-020...
_ID = re.compile(
    r"\b(?:REQ|FEAT|AC|SPEC|TEST|BRIEF|US)-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b"
)

# The literal value passed to a marker: @pytest.mark.requirements("REQ-047-01")
_MARKER_VALUE = {
    name: re.compile(rf"pytest\.mark\.{name}\(\s*[\"']([^\"']+)[\"']")
    for name in ("test_id", "requirements", "scenario")
}


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


def _tracked(ref: str, regex: str) -> list[str]:
    """Paths under ``ref`` whose full path matches ``regex`` (a real regex)."""
    out = _git("ls-tree", "-r", "--name-only", ref)
    compiled = re.compile(regex)
    return sorted(line for line in out.splitlines() if compiled.match(line))


def build_spec_index(ref: str) -> set[str]:
    """Collect every id mentioned anywhere in the spec corpus."""
    ids: set[str] = set()
    for pattern in SPEC_PATH_PATTERNS:
        for path in _tracked(ref, pattern):
            try:
                text = _git("show", f"{ref}:{path}")
            except RuntimeError:
                continue
            ids.update(_ID.findall(text))
    return ids


def _test_files(ref: str, include_worktree: bool) -> dict[str, str]:
    if include_worktree:
        sources: dict[str, str] = {}
        for tree in TEST_TREES:
            root = REPO_ROOT / tree
            if not root.is_dir():
                continue
            for path in root.rglob("test_*.py"):
                sources[path.relative_to(REPO_ROOT).as_posix()] = path.read_text(
                    encoding="utf-8-sig", errors="replace"
                )
        return sources

    sources = {}
    for tree in TEST_TREES:
        for path in _tracked(ref, re.escape(tree) + r"/.*\.py$"):
            if path.rsplit("/", 1)[-1].startswith("test_"):
                sources[path] = _git("show", f"{ref}:{path}")
    return sources


def _marker_value(block: str, name: str) -> str | None:
    found = _MARKER_VALUE[name].search(block)
    return found.group(1) if found else None


def build_report(ref: str = "HEAD", include_worktree: bool = False) -> dict:
    """Scan the test trees and resolve every marker against the spec corpus."""
    spec_index = build_spec_index(ref)
    sources = _test_files(ref, include_worktree)

    total = 0
    compliant = 0
    unresolved: list[dict] = []
    by_tree: dict[str, dict[str, int]] = {}
    by_file: dict[str, int] = {}
    files_missing: set[str] = set()
    id_owners: dict[str, list[str]] = {}

    for rel in sorted(sources):
        tree = rel.split("/", 1)[0]
        bucket = by_tree.setdefault(
            tree, {"test_functions": 0, "with_all_three_markers": 0}
        )
        file_compliant = 0
        lines = sources[rel].lstrip("﻿").splitlines()
        for index, line in enumerate(lines):
            if not _TEST_DEF.match(line):
                continue
            total += 1
            bucket["test_functions"] += 1
            block = _decorator_block(lines, index)
            name = _TEST_DEF.match(line).group(1)
            where = f"{rel}::{name}"

            # A marker that is absent is a COVERAGE gap, not an unresolved
            # reference. Only a present-but-dangling value is a resolution
            # failure; conflating the two would misreport both.
            for marker in ("requirements", "scenario"):
                value = _marker_value(block, marker)
                if value and value not in spec_index:
                    unresolved.append(
                        {"test": where, "marker": marker, "value": value}
                    )
            test_id = _marker_value(block, "test_id")
            if test_id:
                id_owners.setdefault(test_id, []).append(where)

            if not missing_markers(block):
                compliant += 1
                file_compliant += 1
                bucket["with_all_three_markers"] += 1
            else:
                files_missing.add(rel)
        if file_compliant:
            by_file[rel] = file_compliant

    for bucket in by_tree.values():
        total_in = bucket["test_functions"]
        bucket["compliant_percent"] = (
            round(100 * bucket["with_all_three_markers"] / total_in, 1) if total_in else 0.0
        )

    duplicate_ids = {
        test_id: owners for test_id, owners in sorted(id_owners.items()) if len(owners) > 1
    }
    percent = round(100 * compliant / total, 1) if total else 0.0
    return {
        "schema_version": "1.0",
        "generated_by": "scripts/traceability_runner.py",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "working_tree" if include_worktree else "committed_tree",
        "ref": "working_tree" if include_worktree else ref,
        "commit": None if include_worktree else _git("rev-parse", ref).strip(),
        "test_trees_scanned": list(TEST_TREES),
        "test_files_total": len(sources),
        "test_functions_total": total,
        "functions_with_all_three_markers": compliant,
        "compliant_percent": percent,
        "files_with_noncompliant_tests": len(files_missing),
        "by_test_tree": by_tree,
        # Per-file compliant counts. The gate compares these against the
        # recorded commit to detect a LOST marker. Whole-suite totals cannot
        # do that job: a newly added compliant test raises the total and
        # cancels out a deletion elsewhere.
        "by_file_compliant": by_file,
        "spec_ids_indexed": len(spec_index),
        "spec_references": {
            # requirements + scenario only; test_id is not a spec reference.
            "unresolved_count": len(unresolved),
            "unresolved": unresolved,
        },
        "test_id_identity": {
            "distinct_ids": len(id_owners),
            "duplicate_count": len(duplicate_ids),
            "duplicates": duplicate_ids,
        },
        # Kept in lockstep with count_traceability_coverage.measure()'s own
        # verdict, so the two instruments cannot disagree about scope.
        "enforcement_scope": measure_coverage(
            ref=ref, include_worktree=include_worktree
        )["enforcement_scope"],
    }


def render(report: dict) -> str:
    lines = [
        "VERITAS traceability runner (ZOO-21)",
        f"  scope:                            {report['scope']} @ {report['ref']}",
        f"  test trees:                       {', '.join(report['test_trees_scanned'])}",
        f"  test files:                       {report['test_files_total']}",
        f"  test functions:                   {report['test_functions_total']}",
        f"  with all three markers:           "
        f"{report['functions_with_all_three_markers']} "
        f"({report['compliant_percent']}%)",
        f"  spec ids indexed:                 {report['spec_ids_indexed']}",
        f"  unresolved spec references:       {report['spec_references']['unresolved_count']}",
        f"  duplicate test ids:               {report['test_id_identity']['duplicate_count']}",
    ]
    for tree, bucket in sorted(report["by_test_tree"].items()):
        lines.append(
            f"    {tree}: {bucket['with_all_three_markers']}/"
            f"{bucket['test_functions']} ({bucket['compliant_percent']}%)"
        )
    if report["spec_references"]["unresolved_count"]:
        lines.append("  unresolved spec references (marker -> id in no spec file):")
        for item in report["spec_references"]["unresolved"][:10]:
            lines.append(f"    {item['test']}  {item['marker']}={item['value']}")
    if report["test_id_identity"]["duplicate_count"]:
        lines.append("  duplicate test ids (a test id must identify exactly one test):")
        for test_id, owners in report["test_id_identity"]["duplicates"].items():
            lines.append(f"    {test_id}: {', '.join(owners)}")
    return "\n".join(lines)


def write_artifact(report: dict, path: Path = ARTIFACT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the report to stdout as JSON (still writes the artifact)",
    )
    parser.add_argument(
        "--ref", default="HEAD", help="commit to measure (default: HEAD)"
    )
    parser.add_argument(
        "--include-worktree",
        action="store_true",
        help="measure the working tree instead of a committed tree (default)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ARTIFACT,
        help=f"artifact path (default: {ARTIFACT.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 if the artifact is missing or stale",
    )
    args = parser.parse_args()

    report = build_report(ref=args.ref, include_worktree=args.include_worktree)

    if args.check:
        # Staleness is judged against the commit the artifact itself claims,
        # NOT against HEAD. Re-deriving the recorded measurement is
        # deterministic: it cannot change while this check runs, and it cannot
        # be moved by a concurrent commit in a shared workspace. Checking
        # against HEAD instead would fail every unrelated commit that lands
        # after the artifact was written, which is the same mid-test drift the
        # coverage counter's --ref was introduced to avoid.
        if not args.output.is_file():
            print(f"[FAIL] No traceability artifact at {args.output}")
            return 1
        try:
            existing = json.loads(args.output.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[FAIL] Unreadable traceability artifact: {exc}")
            return 1
        recorded = existing.get("commit")
        if existing.get("scope") == "working_tree" or not recorded:
            print("[FAIL] Artifact does not record the commit it was generated from.")
            return 1
        fresh = build_report(ref=recorded)
        drift = [
            key
            for key in (
                "commit",
                "test_functions_total",
                "functions_with_all_three_markers",
                "compliant_percent",
                "files_with_noncompliant_tests",
                "spec_references",
                "test_id_identity",
                "by_file_compliant",
            )
            if existing.get(key) != fresh.get(key)
        ]
        if drift:
            print(f"[FAIL] Stale traceability artifact; fields differ: {drift}")
            return 1
        print(
            f"[PASS] Traceability artifact reproduces at {recorded[:7]} "
            f"({fresh['compliant_percent']}% marker coverage)."
        )
        return 0

    written = write_artifact(report, args.output)
    if args.json:
        # stdout is the machine-readable channel; the human report goes to
        # stderr so `--json | jq` is never polluted by prose.
        print(json.dumps(report, indent=2, sort_keys=True))
        print(f"artifact: {written.relative_to(REPO_ROOT)}", file=sys.stderr)
    else:
        print(render(report))
        print(f"  artifact:                         {written.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
