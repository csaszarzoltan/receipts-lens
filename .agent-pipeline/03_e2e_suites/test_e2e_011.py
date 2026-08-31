"""
E2E Test Suite for FEAT-011
Related Spec: docs/specs/SPEC-011-kategorizalas-es-haztartasi-konyvelesi-besorolas.md
Related Brief: briefs/BRIEF-011-kategorizalas-es-haztartasi-konyvelesi-besorolas.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_011_ac_011_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-011-01 [MUST]
      - Scenario: AC-011-01
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/categorize', 'MUST')


async def test_e2e_011_ac_011_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-011-02 [MUST]
      - Scenario: AC-011-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/categories', 'MUST')


async def test_e2e_011_ac_011_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-011-03 [MUST]
      - Scenario: AC-011-03
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/receipts/{id}/category', 'MUST')


async def test_e2e_011_ac_011_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-011-04 [MUST]
      - Scenario: AC-011-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/categorize', 'MUST')


async def test_e2e_011_ac_011_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-011-05 [MUST NOT]
      - Scenario: AC-011-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/categories', 'MUST NOT')


async def test_e2e_011_ac_011_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-011-06 [ALWAYS]
      - Scenario: AC-011-06
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/receipts/{id}/category', 'ALWAYS')


async def test_e2e_011_ac_011_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-011-07 [CONCURRENCY]
      - Scenario: AC-011-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/categorize', 'CONCURRENCY')


async def test_e2e_011_gui_flow():
    """
    Traceability:
      - Requirement: REQ-011-01 [MUST]
      - Scenario: AC-011-01
    """
    await browser_smoke('/')

