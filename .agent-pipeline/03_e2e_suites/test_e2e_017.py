"""
E2E Test Suite for FEAT-017
Related Spec: docs/specs/SPEC-017-konyvelo-meghivasa-es-biztonsagos-megosztas.md
Related Brief: briefs/BRIEF-017-konyvelo-meghivasa-es-biztonsagos-megosztas.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_017_ac_017_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-01 [MUST]
      - Scenario: AC-017-01
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/accountant/invite', 'MUST')


async def test_e2e_017_ac_017_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-02 [MUST]
      - Scenario: AC-017-02
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/accountant/access/{token}', 'MUST')


async def test_e2e_017_ac_017_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-03 [MUST]
      - Scenario: AC-017-03
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/accountant/access/{id}', 'MUST')


async def test_e2e_017_ac_017_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-04 [MUST]
      - Scenario: AC-017-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/accountant/invite', 'MUST')


async def test_e2e_017_ac_017_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-05 [MUST]
      - Scenario: AC-017-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/accountant/access/{token}', 'MUST')


async def test_e2e_017_ac_017_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-06 [MUST NOT]
      - Scenario: AC-017-06
    """
    await exercise_scenario(async_client, 'DELETE', '/api/v2/accountant/access/{id}', 'MUST NOT')


async def test_e2e_017_ac_017_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-07 [ALWAYS]
      - Scenario: AC-017-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/accountant/invite', 'ALWAYS')


async def test_e2e_017_ac_017_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-017-08 [CONCURRENCY]
      - Scenario: AC-017-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/accountant/access/{token}', 'CONCURRENCY')


async def test_e2e_017_gui_flow():
    """
    Traceability:
      - Requirement: REQ-017-01 [MUST]
      - Scenario: AC-017-01
    """
    await browser_smoke('/')

