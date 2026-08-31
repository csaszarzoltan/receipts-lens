"""
E2E Test Suite for FEAT-004
Related Spec: docs/specs/SPEC-004-kezdeti-beallitas-es-elso-nyugta.md
Related Brief: briefs/BRIEF-004-kezdeti-beallitas-es-elso-nyugta.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_004_ac_004_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-01 [MUST]
      - Scenario: AC-004-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/onboarding/status', 'MUST')


async def test_e2e_004_ac_004_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-02 [MUST]
      - Scenario: AC-004-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/onboarding/complete', 'MUST')


async def test_e2e_004_ac_004_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-03 [MUST]
      - Scenario: AC-004-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/onboarding/first-receipt', 'MUST')


async def test_e2e_004_ac_004_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-04 [MUST]
      - Scenario: AC-004-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/onboarding/status', 'MUST')


async def test_e2e_004_ac_004_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-05 [MUST]
      - Scenario: AC-004-05
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/onboarding/complete', 'MUST')


async def test_e2e_004_ac_004_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-06 [MUST NOT]
      - Scenario: AC-004-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/onboarding/first-receipt', 'MUST NOT')


async def test_e2e_004_ac_004_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-07 [ALWAYS]
      - Scenario: AC-004-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/onboarding/status', 'ALWAYS')


async def test_e2e_004_ac_004_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-004-08 [CONCURRENCY]
      - Scenario: AC-004-08
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/onboarding/complete', 'CONCURRENCY')


async def test_e2e_004_gui_flow():
    """
    Traceability:
      - Requirement: REQ-004-01 [MUST]
      - Scenario: AC-004-01
    """
    await browser_smoke('/')

