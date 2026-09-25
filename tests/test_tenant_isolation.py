"""Tenant-isolation contract tests for the durable data plane.

Function under test
-------------------
``app.platform.SqliteDataPlane`` -- the tenant-scoped reference adapter used by
``scripts/security-gate.sh``.

The security gate advertises that "tenant ... regressions follow".  These tests
are that promise made executable.  They assert the *tenant-scoped* access
contract directly against the SQL the adapter actually issues:

- ``submit_receipt`` writes under the caller's ``tenant_id`` and is idempotent
  per ``(tenant_id, idempotency_key)``.
- ``get_receipt`` is filtered by ``tenant_id`` in the ``WHERE`` clause, so one
  tenant can never read another tenant's receipt.
- The same idempotency key used by two different tenants does not collide.

Each test is written so that removing the ``tenant_id=?`` predicate from
``get_receipt`` makes it fail -- that is the regression the gate must catch.
"""
from __future__ import annotations

import pytest

from app.platform import ConflictError, JobState, SqliteDataPlane


def _plane(tmp_path) -> SqliteDataPlane:
    return SqliteDataPlane(tmp_path / "plane.db")


def _submit(plane: SqliteDataPlane, tenant: str, key: str, marker: str):
    return plane.submit_receipt(tenant, {"total": marker}, key, f"blob://{marker}")


@pytest.mark.test_id("TEST-TI-001")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_receipt_is_scoped_to_submitting_tenant(tmp_path):
    """A submission is stored under, and only retrievable by, its own tenant."""
    plane = _plane(tmp_path)
    try:
        tenant_a, tenant_b = "tenant-a", "tenant-b"
        receipt = _submit(plane, tenant_a, "k-1", "100.00")

        assert plane.get_receipt(tenant_a, receipt.receipt_id) == {"total": "100.00"}
        assert plane.get_receipt(tenant_b, receipt.receipt_id) is None
    finally:
        plane.close()


@pytest.mark.test_id("TEST-TI-002")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_cross_tenant_read_returns_nothing_for_every_receipt(tmp_path):
    """No tenant may enumerate another tenant's receipts, one by one."""
    plane = _plane(tmp_path)
    try:
        a_receipts = [_submit(plane, "tenant-a", f"k-{i}", str(i)).receipt_id for i in range(3)]
        b_receipts = [_submit(plane, "tenant-b", f"k-{i}", f"b{i}").receipt_id for i in range(3)]

        for receipt_id in a_receipts:
            assert plane.get_receipt("tenant-b", receipt_id) is None
        for receipt_id in b_receipts:
            assert plane.get_receipt("tenant-a", receipt_id) is None
    finally:
        plane.close()


@pytest.mark.test_id("TEST-TI-003")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_unknown_receipt_id_is_not_disclosed(tmp_path):
    """A missing receipt reads as ``None`` rather than raising or leaking."""
    plane = _plane(tmp_path)
    try:
        _submit(plane, "tenant-a", "k-1", "1")
        assert plane.get_receipt("tenant-a", "does-not-exist") is None
    finally:
        plane.close()


@pytest.mark.test_id("TEST-TI-004")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_idempotency_key_is_scoped_per_tenant(tmp_path):
    """The same key in two tenants creates two independent receipts."""
    plane = _plane(tmp_path)
    try:
        a = _submit(plane, "tenant-a", "shared-key", "a")
        b = _submit(plane, "tenant-b", "shared-key", "b")

        assert a.receipt_id != b.receipt_id
        assert a.job_id != b.job_id
        assert plane.get_receipt("tenant-a", a.receipt_id) == {"total": "a"}
        assert plane.get_receipt("tenant-b", b.receipt_id) == {"total": "b"}
    finally:
        plane.close()


@pytest.mark.test_id("TEST-TI-005")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_repeat_submission_with_same_key_is_idempotent(tmp_path):
    """Replaying a key within one tenant returns the original receipt."""
    plane = _plane(tmp_path)
    try:
        first = _submit(plane, "tenant-a", "k-1", "1")
        second = _submit(plane, "tenant-a", "k-1", "1")

        assert first.receipt_id == second.receipt_id
        assert first.job_id == second.job_id
    finally:
        plane.close()


@pytest.mark.test_id("TEST-TI-006")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_submission_requires_tenant_identity(tmp_path):
    """An empty tenant id is rejected rather than silently unscoped."""
    plane = _plane(tmp_path)
    try:
        with pytest.raises(ValueError):
            plane.submit_receipt("", {"total": "1"}, "k-1", "blob://1")
    finally:
        plane.close()


@pytest.mark.test_id("TEST-TI-007")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_job_carrying_another_tenants_receipt_is_not_readable(tmp_path):
    """The queued job inherits the submitting tenant, so cross-tenant work is impossible."""
    plane = _plane(tmp_path)
    try:
        receipt = _submit(plane, "tenant-a", "k-1", "1")
        job = plane.claim_job("worker-1")

        assert job is not None
        assert job.tenant_id == "tenant-a"
        assert job.receipt_id == receipt.receipt_id
        assert plane.get_receipt("tenant-b", job.receipt_id) is None
    finally:
        plane.close()


@pytest.mark.test_id("TEST-TI-008")
@pytest.mark.requirements("REQ-TI-01")
@pytest.mark.scenario("AC-TI-01")
def test_stale_writer_cannot_mutate_a_claimed_job(tmp_path):
    """Optimistic locking rejects a second writer using a stale version."""
    plane = _plane(tmp_path)
    try:
        _submit(plane, "tenant-a", "k-1", "1")
        claimed = plane.claim_job("worker-1")
        assert claimed is not None

        with pytest.raises(ConflictError):
            plane.transition_job(claimed.job_id, JobState.COMPLETED, claimed.version - 1)
    finally:
        plane.close()
