"""Deterministic audit for SPEC -> REQ/AC -> executable E2E traceability."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "docs" / "specs"
SUITES = ROOT / ".agent-pipeline" / "03_e2e_suites"


def test_every_feature_has_exactly_one_suite():
    index = json.loads((SPECS / "index.json").read_text(encoding="utf-8"))
    expected = {row["feature_id"] for row in index["specifications"]}
    actual = {f"FEAT-{path.stem[-3:]}" for path in SUITES.glob("test_e2e_[0-9][0-9][0-9].py")}
    assert actual == expected


def test_every_requirement_and_scenario_is_traced():
    index = json.loads((SPECS / "index.json").read_text(encoding="utf-8"))
    all_req, all_ac, traced_req, traced_ac = set(), set(), set(), set()
    for row in index["specifications"]:
        text = (ROOT / row["path"]).read_text(encoding="utf-8")
        all_req.update(re.findall(r"^- (REQ-\d{3}-\d{2}) \[", text, re.M))
        all_ac.update(re.findall(r"^### (AC-\d{3}-\d{2}):", text, re.M))
        suite = SUITES / f"test_e2e_{row['feature_id'][-3:]}.py"
        code = suite.read_text(encoding="utf-8")
        traced_req.update(re.findall(r"Requirement: (REQ-\d{3}-\d{2})", code))
        traced_ac.update(re.findall(r"Scenario: (AC-\d{3}-\d{2})", code))
    assert traced_req == all_req
    assert traced_ac == all_ac
    assert len(all_req) == 296
    assert len(all_ac) == 296


def test_suites_use_only_external_interfaces():
    forbidden = ("sqlite3", "sqlalchemy", "Session(", "get_session", "repository", "monkeypatch")
    for path in SUITES.glob("test_e2e_[0-9][0-9][0-9].py"):
        code = path.read_text(encoding="utf-8")
        assert "exercise_scenario" in code
        assert not any(term in code for term in forbidden)
