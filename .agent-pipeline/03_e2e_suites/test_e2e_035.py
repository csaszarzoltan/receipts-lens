"""
E2E Test Suite for FEAT-035
Related Spec: docs/specs/SPEC-035-ismetlodo-kiadasok-es-elofizetesek-felismerese.md
Related Brief: briefs/BRIEF-035-ismetlodo-kiadasok-es-elofizetesek-felismerese.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_035_ac_035_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-01 [MUST]
      - Scenario: AC-035-01
    """
    await exercise_scenario(async_client, 'GET', '/product/recurring-expenses', 'MUST')


async def test_e2e_035_ac_035_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-02 [MUST]
      - Scenario: AC-035-02
    """
    await exercise_scenario(async_client, 'POST', '/product/recurring-expenses/feedback', 'MUST')


async def test_e2e_035_ac_035_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-03 [MUST]
      - Scenario: AC-035-03
    """
    await exercise_scenario(async_client, 'GET', '/subscriptions', 'MUST')


async def test_e2e_035_ac_035_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-04 [MUST]
      - Scenario: AC-035-04
    """
    await exercise_scenario(async_client, 'GET', '/subscriptions/{subscription_id}/cancel-guide', 'MUST')


async def test_e2e_035_ac_035_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-05 [MUST]
      - Scenario: AC-035-05
    """
    await exercise_scenario(async_client, 'GET', '/product/recurring-expenses', 'MUST')


async def test_e2e_035_ac_035_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-06 [MUST NOT]
      - Scenario: AC-035-06
    """
    await exercise_scenario(async_client, 'POST', '/product/recurring-expenses/feedback', 'MUST NOT')


async def test_e2e_035_ac_035_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-07 [ALWAYS]
      - Scenario: AC-035-07
    """
    await exercise_scenario(async_client, 'GET', '/subscriptions', 'ALWAYS')


async def test_e2e_035_ac_035_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-035-08 [CONCURRENCY]
      - Scenario: AC-035-08
    """
    await exercise_scenario(async_client, 'GET', '/subscriptions/{subscription_id}/cancel-guide', 'CONCURRENCY')

