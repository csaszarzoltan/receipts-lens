"""
E2E Test Suite for FEAT-023
Related Spec: docs/specs/SPEC-023-adozasi-munkaterulet-es-auditcsomag.md
Related Brief: briefs/BRIEF-023-adozasi-munkaterulet-es-auditcsomag.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_023_ac_023_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-01 [MUST]
      - Scenario: AC-023-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/tax/summary', 'MUST')


async def test_e2e_023_ac_023_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-02 [MUST]
      - Scenario: AC-023-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/tax/deductions', 'MUST')


async def test_e2e_023_ac_023_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-03 [MUST]
      - Scenario: AC-023-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/tax/audit-pack', 'MUST')


async def test_e2e_023_ac_023_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-04 [MUST]
      - Scenario: AC-023-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/tax/summary', 'MUST')


async def test_e2e_023_ac_023_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-05 [MUST]
      - Scenario: AC-023-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/tax/deductions', 'MUST')


async def test_e2e_023_ac_023_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-06 [MUST NOT]
      - Scenario: AC-023-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/tax/audit-pack', 'MUST NOT')


async def test_e2e_023_ac_023_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-07 [ALWAYS]
      - Scenario: AC-023-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/tax/summary', 'ALWAYS')


async def test_e2e_023_ac_023_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-023-08 [CONCURRENCY]
      - Scenario: AC-023-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/tax/deductions', 'CONCURRENCY')


async def test_e2e_023_gui_flow():
    """
    Traceability:
      - Requirement: REQ-023-01 [MUST]
      - Scenario: AC-023-01
    """
    await browser_smoke('/')

