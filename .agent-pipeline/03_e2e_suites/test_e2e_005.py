"""
E2E Test Suite for FEAT-005
Related Spec: docs/specs/SPEC-005-haztartasi-attekinto-es-napi-teendok.md
Related Brief: briefs/BRIEF-005-haztartasi-attekinto-es-napi-teendok.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_005_ac_005_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-01 [MUST]
      - Scenario: AC-005-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/summary', 'MUST')


async def test_e2e_005_ac_005_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-02 [MUST]
      - Scenario: AC-005-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/kpis', 'MUST')


async def test_e2e_005_ac_005_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-03 [MUST]
      - Scenario: AC-005-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/actions', 'MUST')


async def test_e2e_005_ac_005_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-04 [MUST]
      - Scenario: AC-005-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/summary', 'MUST')


async def test_e2e_005_ac_005_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-05 [MUST]
      - Scenario: AC-005-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/kpis', 'MUST')


async def test_e2e_005_ac_005_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-06 [MUST NOT]
      - Scenario: AC-005-06
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/actions', 'MUST NOT')


async def test_e2e_005_ac_005_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-07 [ALWAYS]
      - Scenario: AC-005-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/summary', 'ALWAYS')


async def test_e2e_005_ac_005_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-005-08 [CONCURRENCY]
      - Scenario: AC-005-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/dashboard/kpis', 'CONCURRENCY')


async def test_e2e_005_gui_flow():
    """
    Traceability:
      - Requirement: REQ-005-01 [MUST]
      - Scenario: AC-005-01
    """
    await browser_smoke('/')

