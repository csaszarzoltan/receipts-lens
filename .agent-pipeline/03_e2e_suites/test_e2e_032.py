"""
E2E Test Suite for FEAT-032
Related Spec: docs/specs/SPEC-032-nyugta-valtozastortenete-es-auditalhato-javitas.md
Related Brief: briefs/BRIEF-032-nyugta-valtozastortenete-es-auditalhato-javitas.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_032_ac_032_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-032-01 [MUST]
      - Scenario: AC-032-01
    """
    await exercise_scenario(async_client, 'GET', '/product/receipts/{receipt_id}/history', 'MUST')


async def test_e2e_032_ac_032_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-032-02 [MUST]
      - Scenario: AC-032-02
    """
    await exercise_scenario(async_client, 'GET', '/product/receipts/{receipt_id}/history', 'MUST')


async def test_e2e_032_ac_032_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-032-03 [MUST]
      - Scenario: AC-032-03
    """
    await exercise_scenario(async_client, 'GET', '/product/receipts/{receipt_id}/history', 'MUST')


async def test_e2e_032_ac_032_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-032-04 [MUST]
      - Scenario: AC-032-04
    """
    await exercise_scenario(async_client, 'GET', '/product/receipts/{receipt_id}/history', 'MUST')


async def test_e2e_032_ac_032_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-032-05 [MUST NOT]
      - Scenario: AC-032-05
    """
    await exercise_scenario(async_client, 'GET', '/product/receipts/{receipt_id}/history', 'MUST NOT')


async def test_e2e_032_ac_032_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-032-06 [ALWAYS]
      - Scenario: AC-032-06
    """
    await exercise_scenario(async_client, 'GET', '/product/receipts/{receipt_id}/history', 'ALWAYS')


async def test_e2e_032_ac_032_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-032-07 [CONCURRENCY]
      - Scenario: AC-032-07
    """
    await exercise_scenario(async_client, 'GET', '/product/receipts/{receipt_id}/history', 'CONCURRENCY')

