"""Deterministic audit for completed and pending SPEC -> REQ/AC -> E2E traceability."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[2]
SUITES=ROOT/".agent-pipeline"/"03_e2e_suites"
MANIFEST=ROOT/".agent-pipeline"/"00_index"/"manifest.json"

def feature_rows():
 d=json.loads(MANIFEST.read_text(encoding="utf-8")); return [v for k,v in d["tasks"].items() if re.fullmatch(r"SPEC-\d{3}",k)]

def test_every_feature_has_exactly_one_suite():
 for row in feature_rows(): assert (ROOT/row["e2e_test_path"]).is_file(),row["feature_id"]

def test_every_requirement_and_scenario_is_traced():
 for row in feature_rows():
  spec=(ROOT/row["spec_path"]).read_text(encoding="utf-8"); suite=(ROOT/row["e2e_test_path"]).read_text(encoding="utf-8")
  req=set(re.findall(r"^- (REQ-\d{3}-\d{2}) \[",spec,re.M)); ac=set(re.findall(r"^### (AC-\d{3}-\d{2}):",spec,re.M))
  traced_req=set(re.findall(r"(?:Requirement: |@requirement:)(REQ-\d{3}-\d{2})",suite)); traced_ac=set(re.findall(r"(?:Scenario: |@scenario:)(AC-\d{3}-\d{2})",suite))
  assert req==traced_req,(row["feature_id"],req-traced_req,traced_req-req); assert ac==traced_ac,(row["feature_id"],ac-traced_ac,traced_ac-ac)

def test_suites_use_only_external_interfaces():
 forbidden=("sqlite3","sqlalchemy","Session(","get_session","repository","monkeypatch","from app")
 for row in feature_rows():
  code=(ROOT/row["e2e_test_path"]).read_text(encoding="utf-8"); assert ("exercise_scenario" in code or "httpx" in code); assert not any(x in code for x in forbidden)
