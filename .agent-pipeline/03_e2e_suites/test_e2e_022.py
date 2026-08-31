"""
E2E Test Suite for FEAT-022
Related Spec: docs/specs/SPEC-022-elofizetes-kvota-es-hasznalati-korlatok.md
Related Brief: briefs/BRIEF-022-elofizetes-kvota-es-hasznalati-korlatok.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_022_ac_022_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-01 [MUST]
      - Scenario: AC-022-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/subscriptions/me', 'MUST')


async def test_e2e_022_ac_022_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-02 [MUST]
      - Scenario: AC-022-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/quota/usage', 'MUST')


async def test_e2e_022_ac_022_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-03 [MUST]
      - Scenario: AC-022-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/subscriptions/upgrade', 'MUST')


async def test_e2e_022_ac_022_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-04 [MUST]
      - Scenario: AC-022-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/subscriptions/me', 'MUST')


async def test_e2e_022_ac_022_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-05 [MUST]
      - Scenario: AC-022-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/quota/usage', 'MUST')


async def test_e2e_022_ac_022_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-06 [MUST NOT]
      - Scenario: AC-022-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/subscriptions/upgrade', 'MUST NOT')


async def test_e2e_022_ac_022_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-07 [ALWAYS]
      - Scenario: AC-022-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/subscriptions/me', 'ALWAYS')


async def test_e2e_022_ac_022_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-022-08 [CONCURRENCY]
      - Scenario: AC-022-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/quota/usage', 'CONCURRENCY')


async def test_e2e_022_gui_flow():
    """
    Traceability:
      - Requirement: REQ-022-01 [MUST]
      - Scenario: AC-022-01
    """
    await browser_smoke('/')

