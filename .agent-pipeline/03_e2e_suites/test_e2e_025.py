"""
E2E Test Suite for FEAT-025
Related Spec: docs/specs/SPEC-025-adatvedelem-megorzes-es-torles.md
Related Brief: briefs/BRIEF-025-adatvedelem-megorzes-es-torles.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_025_ac_025_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-01 [MUST]
      - Scenario: AC-025-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/privacy/data-export', 'MUST')


async def test_e2e_025_ac_025_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-02 [MUST]
      - Scenario: AC-025-02
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/privacy/account', 'MUST')


async def test_e2e_025_ac_025_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-03 [MUST]
      - Scenario: AC-025-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/privacy/retention', 'MUST')


async def test_e2e_025_ac_025_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-04 [MUST]
      - Scenario: AC-025-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/privacy/data-export', 'MUST')


async def test_e2e_025_ac_025_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-05 [MUST]
      - Scenario: AC-025-05
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/privacy/account', 'MUST')


async def test_e2e_025_ac_025_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-06 [MUST NOT]
      - Scenario: AC-025-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/privacy/retention', 'MUST NOT')


async def test_e2e_025_ac_025_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-07 [ALWAYS]
      - Scenario: AC-025-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/privacy/data-export', 'ALWAYS')


async def test_e2e_025_ac_025_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-025-08 [CONCURRENCY]
      - Scenario: AC-025-08
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/privacy/account', 'CONCURRENCY')


async def test_e2e_025_gui_flow():
    """
    Traceability:
      - Requirement: REQ-025-01 [MUST]
      - Scenario: AC-025-01
    """
    await browser_smoke('/')

