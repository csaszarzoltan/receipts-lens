"""
E2E Test Suite for FEAT-026
Related Spec: docs/specs/SPEC-026-ertesitesek-es-allapotuzenetek.md
Related Brief: briefs/BRIEF-026-ertesitesek-es-allapotuzenetek.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_026_ac_026_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-01 [MUST]
      - Scenario: AC-026-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/notifications', 'MUST')


async def test_e2e_026_ac_026_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-02 [MUST]
      - Scenario: AC-026-02
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/notifications/{id}/read', 'MUST')


async def test_e2e_026_ac_026_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-03 [MUST]
      - Scenario: AC-026-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/notifications/mark-all-read', 'MUST')


async def test_e2e_026_ac_026_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-04 [MUST]
      - Scenario: AC-026-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/notifications', 'MUST')


async def test_e2e_026_ac_026_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-05 [MUST]
      - Scenario: AC-026-05
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/notifications/{id}/read', 'MUST')


async def test_e2e_026_ac_026_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-06 [MUST NOT]
      - Scenario: AC-026-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/notifications/mark-all-read', 'MUST NOT')


async def test_e2e_026_ac_026_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-07 [ALWAYS]
      - Scenario: AC-026-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/notifications', 'ALWAYS')


async def test_e2e_026_ac_026_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-026-08 [CONCURRENCY]
      - Scenario: AC-026-08
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/notifications/{id}/read', 'CONCURRENCY')

