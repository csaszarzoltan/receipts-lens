"""
E2E Test Suite for FEAT-018
Related Spec: docs/specs/SPEC-018-kulso-szolgaltatasok-csatlakoztatasa.md
Related Brief: briefs/BRIEF-018-kulso-szolgaltatasok-csatlakoztatasa.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_018_ac_018_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-01 [MUST]
      - Scenario: AC-018-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/integrations', 'MUST')


async def test_e2e_018_ac_018_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-02 [MUST]
      - Scenario: AC-018-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/integrations/{id}/connect', 'MUST')


async def test_e2e_018_ac_018_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-03 [MUST]
      - Scenario: AC-018-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/integrations/{id}/callback', 'MUST')


async def test_e2e_018_ac_018_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-04 [MUST]
      - Scenario: AC-018-04
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/integrations/{id}/disconnect', 'MUST')


async def test_e2e_018_ac_018_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-05 [MUST]
      - Scenario: AC-018-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/integrations', 'MUST')


async def test_e2e_018_ac_018_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-06 [MUST NOT]
      - Scenario: AC-018-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/integrations/{id}/connect', 'MUST NOT')


async def test_e2e_018_ac_018_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-07 [ALWAYS]
      - Scenario: AC-018-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/integrations/{id}/callback', 'ALWAYS')


async def test_e2e_018_ac_018_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-018-08 [CONCURRENCY]
      - Scenario: AC-018-08
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/integrations/{id}/disconnect', 'CONCURRENCY')


async def test_e2e_018_gui_flow():
    """
    Traceability:
      - Requirement: REQ-018-01 [MUST]
      - Scenario: AC-018-01
    """
    await browser_smoke('/')

