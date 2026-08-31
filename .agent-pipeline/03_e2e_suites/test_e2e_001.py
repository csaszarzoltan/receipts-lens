"""
E2E Test Suite for FEAT-001
Related Spec: docs/specs/SPEC-001-nyilvanos-bemutatkozas-es-belepesi-utvonal.md
Related Brief: briefs/BRIEF-001-nyilvanos-bemutatkozas-es-belepesi-utvonal.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_001_ac_001_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-001-01 [MUST]
      - Scenario: AC-001-01
    """
    await exercise_scenario(async_client, 'GET', '/', 'MUST')


async def test_e2e_001_ac_001_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-001-02 [MUST]
      - Scenario: AC-001-02
    """
    await exercise_scenario(async_client, 'GET', '/health', 'MUST')


async def test_e2e_001_ac_001_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-001-03 [MUST]
      - Scenario: AC-001-03
    """
    await exercise_scenario(async_client, 'GET', '/', 'MUST')


async def test_e2e_001_ac_001_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-001-04 [MUST]
      - Scenario: AC-001-04
    """
    await exercise_scenario(async_client, 'GET', '/health', 'MUST')


async def test_e2e_001_ac_001_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-001-05 [MUST NOT]
      - Scenario: AC-001-05
    """
    await exercise_scenario(async_client, 'GET', '/', 'MUST NOT')


async def test_e2e_001_ac_001_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-001-06 [ALWAYS]
      - Scenario: AC-001-06
    """
    await exercise_scenario(async_client, 'GET', '/health', 'ALWAYS')


async def test_e2e_001_ac_001_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-001-07 [CONCURRENCY]
      - Scenario: AC-001-07
    """
    await exercise_scenario(async_client, 'GET', '/', 'CONCURRENCY')


async def test_e2e_001_gui_flow():
    """
    Traceability:
      - Requirement: REQ-001-01 [MUST]
      - Scenario: AC-001-01
    """
    await browser_smoke('/')

