"""
E2E Test Suite for FEAT-013
Related Spec: docs/specs/SPEC-013-koltesi-elemzes-es-elorejelzes.md
Related Brief: briefs/BRIEF-013-koltesi-elemzes-es-elorejelzes.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_013_ac_013_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-01 [MUST]
      - Scenario: AC-013-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/analytics/spending', 'MUST')


async def test_e2e_013_ac_013_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-02 [MUST]
      - Scenario: AC-013-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/forecast/monthly', 'MUST')


async def test_e2e_013_ac_013_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-03 [MUST]
      - Scenario: AC-013-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/analytics/spending', 'MUST')


async def test_e2e_013_ac_013_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-04 [MUST]
      - Scenario: AC-013-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/forecast/monthly', 'MUST')


async def test_e2e_013_ac_013_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-05 [MUST]
      - Scenario: AC-013-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/analytics/spending', 'MUST')


async def test_e2e_013_ac_013_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-06 [MUST NOT]
      - Scenario: AC-013-06
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/forecast/monthly', 'MUST NOT')


async def test_e2e_013_ac_013_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-07 [ALWAYS]
      - Scenario: AC-013-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/analytics/spending', 'ALWAYS')


async def test_e2e_013_ac_013_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-013-08 [CONCURRENCY]
      - Scenario: AC-013-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/forecast/monthly', 'CONCURRENCY')


async def test_e2e_013_gui_flow():
    """
    Traceability:
      - Requirement: REQ-013-01 [MUST]
      - Scenario: AC-013-01
    """
    await browser_smoke('/')

