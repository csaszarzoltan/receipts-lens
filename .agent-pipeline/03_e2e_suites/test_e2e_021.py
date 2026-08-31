"""
E2E Test Suite for FEAT-021
Related Spec: docs/specs/SPEC-021-automatizalasok-es-feldolgozasi-szabalyok.md
Related Brief: briefs/BRIEF-021-automatizalasok-es-feldolgozasi-szabalyok.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_021_ac_021_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-01 [MUST]
      - Scenario: AC-021-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/automations', 'MUST')


async def test_e2e_021_ac_021_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-02 [MUST]
      - Scenario: AC-021-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/automations', 'MUST')


async def test_e2e_021_ac_021_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-03 [MUST]
      - Scenario: AC-021-03
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/automations/{id}', 'MUST')


async def test_e2e_021_ac_021_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-04 [MUST]
      - Scenario: AC-021-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/automations/{id}/runs', 'MUST')


async def test_e2e_021_ac_021_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-05 [MUST]
      - Scenario: AC-021-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/automations', 'MUST')


async def test_e2e_021_ac_021_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-06 [MUST NOT]
      - Scenario: AC-021-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/automations', 'MUST NOT')


async def test_e2e_021_ac_021_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-07 [ALWAYS]
      - Scenario: AC-021-07
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/automations/{id}', 'ALWAYS')


async def test_e2e_021_ac_021_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-021-08 [CONCURRENCY]
      - Scenario: AC-021-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/automations/{id}/runs', 'CONCURRENCY')


async def test_e2e_021_gui_flow():
    """
    Traceability:
      - Requirement: REQ-021-01 [MUST]
      - Scenario: AC-021-01
    """
    await browser_smoke('/')

