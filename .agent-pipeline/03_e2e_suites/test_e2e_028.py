"""
E2E Test Suite for FEAT-028
Related Spec: docs/specs/SPEC-028-rendszerallapot-biztonsag-es-mukodesi-atlathatosag.md
Related Brief: briefs/BRIEF-028-rendszerallapot-biztonsag-es-mukodesi-atlathatosag.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_028_ac_028_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-028-01 [MUST]
      - Scenario: AC-028-01
    """
    await exercise_scenario(async_client, 'GET', '/health', 'MUST')


async def test_e2e_028_ac_028_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-028-02 [MUST]
      - Scenario: AC-028-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/system/status', 'MUST')


async def test_e2e_028_ac_028_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-028-03 [MUST]
      - Scenario: AC-028-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/security/audit-log', 'MUST')


async def test_e2e_028_ac_028_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-028-04 [MUST]
      - Scenario: AC-028-04
    """
    await exercise_scenario(async_client, 'GET', '/health', 'MUST')


async def test_e2e_028_ac_028_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-028-05 [MUST NOT]
      - Scenario: AC-028-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/system/status', 'MUST NOT')


async def test_e2e_028_ac_028_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-028-06 [ALWAYS]
      - Scenario: AC-028-06
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/security/audit-log', 'ALWAYS')


async def test_e2e_028_ac_028_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-028-07 [CONCURRENCY]
      - Scenario: AC-028-07
    """
    await exercise_scenario(async_client, 'GET', '/health', 'CONCURRENCY')


async def test_e2e_028_gui_flow():
    """
    Traceability:
      - Requirement: REQ-028-01 [MUST]
      - Scenario: AC-028-01
    """
    await browser_smoke('/')

