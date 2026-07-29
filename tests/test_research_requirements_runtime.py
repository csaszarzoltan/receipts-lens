"""Executable acceptance tests for docs/research REQUIREMENTS_01..04."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.governance import AuditChain, AuthContext, RateLimiter, WebhookSigner
from app.integrations import AccountingProfile, CsvAccountingConnector, UsageMeter
from app.platform import ConflictError, JobState, SqliteDataPlane
from app.quality import BenchmarkCase, BenchmarkRunner, ReviewPolicy


def test_data_plane_persists_tenant_scoped_receipts_jobs_and_idempotency(tmp_path: Path) -> None:
    db = tmp_path / "data.db"
    plane = SqliteDataPlane(db)
    result = plane.submit_receipt("tenant-a", {"vendor": "Shop"}, "same-key", "blob://1")
    assert plane.submit_receipt("tenant-a", {"vendor": "Changed"}, "same-key", "blob://2") == result
    job = plane.claim_job("worker-1", lease_seconds=30)
    assert job and job.state is JobState.PROCESSING
    plane.transition_job(job.job_id, JobState.COMPLETED, expected_version=job.version)
    with pytest.raises(ConflictError):
        plane.transition_job(job.job_id, JobState.FAILED, expected_version=job.version)
    plane.close()
    reopened = SqliteDataPlane(db)
    assert reopened.get_receipt("tenant-a", result.receipt_id)["vendor"] == "Shop"
    assert reopened.get_receipt("tenant-b", result.receipt_id) is None


def test_governance_auth_rate_signing_and_audit(tmp_path: Path) -> None:
    context = AuthContext.from_api_key("secret", {"secret": ("tenant-a", "admin")})
    assert context.tenant_id == "tenant-a"
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("tenant-a") and limiter.allow("tenant-a") and not limiter.allow("tenant-a")
    signer = WebhookSigner(b"key", tolerance_seconds=60)
    signature = signer.sign(b"payload", timestamp=100)
    assert signer.verify(b"payload", signature, now=120)
    assert not signer.verify(b"changed", signature, now=120)
    audit = AuditChain(tmp_path / "audit.jsonl")
    first = audit.append("tenant-a", "created", {"receipt_id": "1"})
    second = audit.append("tenant-a", "reviewed", {"receipt_id": "1"})
    assert first.hash != second.hash and audit.verify()


def test_quality_benchmark_review_and_correction_preserve_evidence() -> None:
    cases = [BenchmarkCase("1", {"total": 5.0}, {"total": 5.0}, {"total": 0.4})]
    report = BenchmarkRunner().run("v1", cases)
    assert report.exact_match["total"] == 1.0
    assert report.calibration_ece >= 0
    policy = ReviewPolicy({"total": 0.8})
    assert policy.requires_review(cases[0].prediction, cases[0].confidence)
    corrected = policy.correct(cases[0], {"total": 5.5}, actor="reviewer")
    assert corrected.original_prediction == {"total": 5.0}
    assert corrected.corrected["total"] == 5.5


def test_accounting_connector_usage_and_mapping(tmp_path: Path) -> None:
    meter = UsageMeter(tmp_path / "usage.jsonl")
    meter.record("tenant-a", "receipt.processed", 2)
    assert meter.report("tenant-a")["receipt.processed"] == 2
    profile = AccountingProfile(required_fields=("vendor", "total", "currency"))
    connector = CsvAccountingConnector(profile)
    payload = connector.export([{"vendor": "Shop", "total": 5.0, "currency": "USD"}])
    assert "vendor,total,currency" in payload
    with pytest.raises(ValueError):
        connector.export([{"vendor": "Shop"}])
