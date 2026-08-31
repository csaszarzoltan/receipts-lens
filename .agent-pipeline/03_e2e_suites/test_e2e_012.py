"""
E2E Test Suite for FEAT-012
Related Spec: docs/specs/SPEC-012-haztartasi-keretek-es-riasztasok.md
Related Brief: briefs/BRIEF-012-haztartasi-keretek-es-riasztasok.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_012_ac_012_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-01 [MUST]
      - Scenario: AC-012-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/budgets', 'MUST')


async def test_e2e_012_ac_012_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-02 [MUST]
      - Scenario: AC-012-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/budgets', 'MUST')


async def test_e2e_012_ac_012_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-03 [MUST]
      - Scenario: AC-012-03
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/budgets/{id}', 'MUST')


async def test_e2e_012_ac_012_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-04 [MUST]
      - Scenario: AC-012-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/alerts', 'MUST')


async def test_e2e_012_ac_012_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-05 [MUST]
      - Scenario: AC-012-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/budgets', 'MUST')


async def test_e2e_012_ac_012_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-06 [MUST NOT]
      - Scenario: AC-012-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/budgets', 'MUST NOT')


async def test_e2e_012_ac_012_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-07 [ALWAYS]
      - Scenario: AC-012-07
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/budgets/{id}', 'ALWAYS')


async def test_e2e_012_ac_012_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-012-08 [CONCURRENCY]
      - Scenario: AC-012-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/alerts', 'CONCURRENCY')


async def test_e2e_012_gui_flow():
    """
    Traceability:
      - Requirement: REQ-012-01 [MUST]
      - Scenario: AC-012-01
    """
    await browser_smoke('/')

