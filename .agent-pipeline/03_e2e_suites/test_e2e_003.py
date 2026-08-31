"""
E2E Test Suite for FEAT-003
Related Spec: docs/specs/SPEC-003-google-belepes-es-fiok-osszekapcsolas.md
Related Brief: briefs/BRIEF-003-google-belepes-es-fiok-osszekapcsolas.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_003_ac_003_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-003-01 [MUST]
      - Scenario: AC-003-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/auth/google/login', 'MUST')


async def test_e2e_003_ac_003_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-003-02 [MUST]
      - Scenario: AC-003-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/auth/google/callback', 'MUST')


async def test_e2e_003_ac_003_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-003-03 [MUST]
      - Scenario: AC-003-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/google/exchange', 'MUST')


async def test_e2e_003_ac_003_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-003-04 [MUST]
      - Scenario: AC-003-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/auth/google/login', 'MUST')


async def test_e2e_003_ac_003_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-003-05 [MUST NOT]
      - Scenario: AC-003-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/auth/google/callback', 'MUST NOT')


async def test_e2e_003_ac_003_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-003-06 [ALWAYS]
      - Scenario: AC-003-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/google/exchange', 'ALWAYS')


async def test_e2e_003_ac_003_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-003-07 [CONCURRENCY]
      - Scenario: AC-003-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/auth/google/login', 'CONCURRENCY')


async def test_e2e_003_gui_flow():
    """
    Traceability:
      - Requirement: REQ-003-01 [MUST]
      - Scenario: AC-003-01
    """
    await browser_smoke('/')

