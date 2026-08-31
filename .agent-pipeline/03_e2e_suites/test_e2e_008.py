"""
E2E Test Suite for FEAT-008
Related Spec: docs/specs/SPEC-008-nyugtak-listaja-keresese-es-reszletei.md
Related Brief: briefs/BRIEF-008-nyugtak-listaja-keresese-es-reszletei.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_008_ac_008_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-01 [MUST]
      - Scenario: AC-008-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/receipts', 'MUST')


async def test_e2e_008_ac_008_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-02 [MUST]
      - Scenario: AC-008-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/receipts/{id}', 'MUST')


async def test_e2e_008_ac_008_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-03 [MUST]
      - Scenario: AC-008-03
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/receipts/{id}', 'MUST')


async def test_e2e_008_ac_008_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-04 [MUST]
      - Scenario: AC-008-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/receipts', 'MUST')


async def test_e2e_008_ac_008_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-05 [MUST]
      - Scenario: AC-008-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/receipts/{id}', 'MUST')


async def test_e2e_008_ac_008_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-06 [MUST NOT]
      - Scenario: AC-008-06
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/receipts/{id}', 'MUST NOT')


async def test_e2e_008_ac_008_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-07 [ALWAYS]
      - Scenario: AC-008-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/receipts', 'ALWAYS')


async def test_e2e_008_ac_008_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-008-08 [CONCURRENCY]
      - Scenario: AC-008-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/receipts/{id}', 'CONCURRENCY')


async def test_e2e_008_gui_flow():
    """
    Traceability:
      - Requirement: REQ-008-01 [MUST]
      - Scenario: AC-008-01
    """
    await browser_smoke('/')

