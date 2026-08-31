"""
E2E Test Suite for FEAT-029
Related Spec: docs/specs/SPEC-029-ocr-minoseg-es-adminisztrativ-diagnosztika.md
Related Brief: briefs/BRIEF-029-ocr-minoseg-es-adminisztrativ-diagnosztika.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_029_ac_029_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-029-01 [MUST]
      - Scenario: AC-029-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/diagnostics/ocr-quality', 'MUST')


async def test_e2e_029_ac_029_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-029-02 [MUST]
      - Scenario: AC-029-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/diagnostics/benchmark', 'MUST')


async def test_e2e_029_ac_029_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-029-03 [MUST]
      - Scenario: AC-029-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/diagnostics/ocr-quality', 'MUST')


async def test_e2e_029_ac_029_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-029-04 [MUST]
      - Scenario: AC-029-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/diagnostics/benchmark', 'MUST')


async def test_e2e_029_ac_029_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-029-05 [MUST NOT]
      - Scenario: AC-029-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/diagnostics/ocr-quality', 'MUST NOT')


async def test_e2e_029_ac_029_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-029-06 [ALWAYS]
      - Scenario: AC-029-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/diagnostics/benchmark', 'ALWAYS')


async def test_e2e_029_ac_029_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-029-07 [CONCURRENCY]
      - Scenario: AC-029-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/diagnostics/ocr-quality', 'CONCURRENCY')


async def test_e2e_029_gui_flow():
    """
    Traceability:
      - Requirement: REQ-029-01 [MUST]
      - Scenario: AC-029-01
    """
    await browser_smoke('/')

