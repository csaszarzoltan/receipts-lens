"""
E2E Test Suite for FEAT-010
Related Spec: docs/specs/SPEC-010-ismetlodo-es-duplikalt-nyugtak-kezelese.md
Related Brief: briefs/BRIEF-010-ismetlodo-es-duplikalt-nyugtak-kezelese.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_010_ac_010_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-01 [MUST]
      - Scenario: AC-010-01
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/duplicates/detect', 'MUST')


async def test_e2e_010_ac_010_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-02 [MUST]
      - Scenario: AC-010-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/duplicates', 'MUST')


async def test_e2e_010_ac_010_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-03 [MUST]
      - Scenario: AC-010-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/duplicates/resolve', 'MUST')


async def test_e2e_010_ac_010_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-04 [MUST]
      - Scenario: AC-010-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/duplicates/detect', 'MUST')


async def test_e2e_010_ac_010_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-05 [MUST]
      - Scenario: AC-010-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/duplicates', 'MUST')


async def test_e2e_010_ac_010_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-06 [MUST NOT]
      - Scenario: AC-010-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/duplicates/resolve', 'MUST NOT')


async def test_e2e_010_ac_010_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-07 [ALWAYS]
      - Scenario: AC-010-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/duplicates/detect', 'ALWAYS')


async def test_e2e_010_ac_010_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-010-08 [CONCURRENCY]
      - Scenario: AC-010-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/duplicates', 'CONCURRENCY')


async def test_e2e_010_gui_flow():
    """
    Traceability:
      - Requirement: REQ-010-01 [MUST]
      - Scenario: AC-010-01
    """
    await browser_smoke('/')

