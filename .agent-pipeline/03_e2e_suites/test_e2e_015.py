"""
E2E Test Suite for FEAT-015
Related Spec: docs/specs/SPEC-015-export-elokeszites-es-adatatadas.md
Related Brief: briefs/BRIEF-015-export-elokeszites-es-adatatadas.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_015_ac_015_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-01 [MUST]
      - Scenario: AC-015-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/exports/profiles', 'MUST')


async def test_e2e_015_ac_015_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-02 [MUST]
      - Scenario: AC-015-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/exports/prepare', 'MUST')


async def test_e2e_015_ac_015_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-03 [MUST]
      - Scenario: AC-015-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/exports/execute', 'MUST')


async def test_e2e_015_ac_015_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-04 [MUST]
      - Scenario: AC-015-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/exports/runs/{id}', 'MUST')


async def test_e2e_015_ac_015_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-05 [MUST]
      - Scenario: AC-015-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/exports/profiles', 'MUST')


async def test_e2e_015_ac_015_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-06 [MUST]
      - Scenario: AC-015-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/exports/prepare', 'MUST')


async def test_e2e_015_ac_015_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-07 [MUST NOT]
      - Scenario: AC-015-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/exports/execute', 'MUST NOT')


async def test_e2e_015_ac_015_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-08 [ALWAYS]
      - Scenario: AC-015-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/exports/runs/{id}', 'ALWAYS')


async def test_e2e_015_ac_015_09(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-015-09 [CONCURRENCY]
      - Scenario: AC-015-09
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/exports/profiles', 'CONCURRENCY')


async def test_e2e_015_gui_flow():
    """
    Traceability:
      - Requirement: REQ-015-01 [MUST]
      - Scenario: AC-015-01
    """
    await browser_smoke('/')

