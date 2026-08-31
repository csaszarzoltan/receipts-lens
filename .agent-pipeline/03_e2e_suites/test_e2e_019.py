"""
E2E Test Suite for FEAT-019
Related Spec: docs/specs/SPEC-019-szinkronizalas-es-egyeztetes.md
Related Brief: briefs/BRIEF-019-szinkronizalas-es-egyeztetes.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_019_ac_019_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-01 [MUST]
      - Scenario: AC-019-01
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/sync/trigger', 'MUST')


async def test_e2e_019_ac_019_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-02 [MUST]
      - Scenario: AC-019-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/sync/status', 'MUST')


async def test_e2e_019_ac_019_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-03 [MUST]
      - Scenario: AC-019-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/reconciliation/run', 'MUST')


async def test_e2e_019_ac_019_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-04 [MUST]
      - Scenario: AC-019-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/sync/trigger', 'MUST')


async def test_e2e_019_ac_019_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-05 [MUST]
      - Scenario: AC-019-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/sync/status', 'MUST')


async def test_e2e_019_ac_019_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-06 [MUST NOT]
      - Scenario: AC-019-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/reconciliation/run', 'MUST NOT')


async def test_e2e_019_ac_019_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-07 [ALWAYS]
      - Scenario: AC-019-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/sync/trigger', 'ALWAYS')


async def test_e2e_019_ac_019_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-019-08 [CONCURRENCY]
      - Scenario: AC-019-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/sync/status', 'CONCURRENCY')


async def test_e2e_019_gui_flow():
    """
    Traceability:
      - Requirement: REQ-019-01 [MUST]
      - Scenario: AC-019-01
    """
    await browser_smoke('/')

