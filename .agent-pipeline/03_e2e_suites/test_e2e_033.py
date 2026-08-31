"""
E2E Test Suite for FEAT-033
Related Spec: docs/specs/SPEC-033-szokatlan-koltesek-felismerese-es-magyarazata.md
Related Brief: briefs/BRIEF-033-szokatlan-koltesek-felismerese-es-magyarazata.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_033_ac_033_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-01 [MUST]
      - Scenario: AC-033-01
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'MUST')


async def test_e2e_033_ac_033_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-02 [MUST]
      - Scenario: AC-033-02
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'MUST')


async def test_e2e_033_ac_033_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-03 [MUST]
      - Scenario: AC-033-03
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'MUST')


async def test_e2e_033_ac_033_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-04 [MUST]
      - Scenario: AC-033-04
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'MUST')


async def test_e2e_033_ac_033_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-05 [MUST]
      - Scenario: AC-033-05
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'MUST')


async def test_e2e_033_ac_033_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-06 [MUST NOT]
      - Scenario: AC-033-06
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'MUST NOT')


async def test_e2e_033_ac_033_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-07 [ALWAYS]
      - Scenario: AC-033-07
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'ALWAYS')


async def test_e2e_033_ac_033_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-033-08 [CONCURRENCY]
      - Scenario: AC-033-08
    """
    await exercise_scenario(async_client, 'GET', '/forecasts/anomalies', 'CONCURRENCY')

