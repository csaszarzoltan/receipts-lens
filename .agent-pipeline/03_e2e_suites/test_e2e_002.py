"""
E2E Test Suite for FEAT-002
Related Spec: docs/specs/SPEC-002-fiok-letrehozasa-es-munkamenet.md
Related Brief: briefs/BRIEF-002-fiok-letrehozasa-es-munkamenet.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_002_ac_002_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-01 [MUST]
      - Scenario: AC-002-01
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/register', 'MUST')


async def test_e2e_002_ac_002_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-02 [MUST]
      - Scenario: AC-002-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/login', 'MUST')


async def test_e2e_002_ac_002_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-03 [MUST]
      - Scenario: AC-002-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/magic-link', 'MUST')


async def test_e2e_002_ac_002_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-04 [MUST]
      - Scenario: AC-002-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/refresh', 'MUST')


async def test_e2e_002_ac_002_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-05 [MUST]
      - Scenario: AC-002-05
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/logout', 'MUST')


async def test_e2e_002_ac_002_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-06 [MUST]
      - Scenario: AC-002-06
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/auth/me', 'MUST')


async def test_e2e_002_ac_002_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-07 [MUST NOT]
      - Scenario: AC-002-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/register', 'MUST NOT')


async def test_e2e_002_ac_002_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-08 [ALWAYS]
      - Scenario: AC-002-08
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/login', 'ALWAYS')


async def test_e2e_002_ac_002_09(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-002-09 [CONCURRENCY]
      - Scenario: AC-002-09
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/auth/magic-link', 'CONCURRENCY')


async def test_e2e_002_gui_flow():
    """
    Traceability:
      - Requirement: REQ-002-01 [MUST]
      - Scenario: AC-002-01
    """
    await browser_smoke('/')

