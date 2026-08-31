"""
E2E Test Suite for FEAT-024
Related Spec: docs/specs/SPEC-024-profil-nyelv-penznem-es-megjelenes.md
Related Brief: briefs/BRIEF-024-profil-nyelv-penznem-es-megjelenes.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_024_ac_024_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-01 [MUST]
      - Scenario: AC-024-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/settings/profile', 'MUST')


async def test_e2e_024_ac_024_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-02 [MUST]
      - Scenario: AC-024-02
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/settings/profile', 'MUST')


async def test_e2e_024_ac_024_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-03 [MUST]
      - Scenario: AC-024-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/settings/profile', 'MUST')


async def test_e2e_024_ac_024_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-04 [MUST]
      - Scenario: AC-024-04
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/settings/profile', 'MUST')


async def test_e2e_024_ac_024_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-05 [MUST]
      - Scenario: AC-024-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/settings/profile', 'MUST')


async def test_e2e_024_ac_024_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-06 [MUST]
      - Scenario: AC-024-06
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/settings/profile', 'MUST')


async def test_e2e_024_ac_024_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-07 [MUST NOT]
      - Scenario: AC-024-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/settings/profile', 'MUST NOT')


async def test_e2e_024_ac_024_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-08 [ALWAYS]
      - Scenario: AC-024-08
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/settings/profile', 'ALWAYS')


async def test_e2e_024_ac_024_09(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-024-09 [CONCURRENCY]
      - Scenario: AC-024-09
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/settings/profile', 'CONCURRENCY')


async def test_e2e_024_gui_flow():
    """
    Traceability:
      - Requirement: REQ-024-01 [MUST]
      - Scenario: AC-024-01
    """
    await browser_smoke('/')

