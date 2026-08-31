"""
E2E Test Suite for FEAT-014
Related Spec: docs/specs/SPEC-014-jelentesek-letrehozasa-es-letoltese.md
Related Brief: briefs/BRIEF-014-jelentesek-letrehozasa-es-letoltese.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_014_ac_014_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-014-01 [MUST]
      - Scenario: AC-014-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/reports/summary', 'MUST')


async def test_e2e_014_ac_014_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-014-02 [MUST]
      - Scenario: AC-014-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/reports/generate-pdf', 'MUST')


async def test_e2e_014_ac_014_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-014-03 [MUST]
      - Scenario: AC-014-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/reports/download/{id}', 'MUST')


async def test_e2e_014_ac_014_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-014-04 [MUST]
      - Scenario: AC-014-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/reports/summary', 'MUST')


async def test_e2e_014_ac_014_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-014-05 [MUST NOT]
      - Scenario: AC-014-05
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/reports/generate-pdf', 'MUST NOT')


async def test_e2e_014_ac_014_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-014-06 [ALWAYS]
      - Scenario: AC-014-06
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/reports/download/{id}', 'ALWAYS')


async def test_e2e_014_ac_014_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-014-07 [CONCURRENCY]
      - Scenario: AC-014-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/reports/summary', 'CONCURRENCY')


async def test_e2e_014_gui_flow():
    """
    Traceability:
      - Requirement: REQ-014-01 [MUST]
      - Scenario: AC-014-01
    """
    await browser_smoke('/')

