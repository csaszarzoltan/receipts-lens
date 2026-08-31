"""
E2E Test Suite for FEAT-030
Related Spec: docs/specs/SPEC-030-jelszo-nelkuli-belepes-e-mailes-hivatkozassal.md
Related Brief: briefs/BRIEF-030-jelszo-nelkuli-belepes-e-mailes-hivatkozassal.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_030_ac_030_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-030-01 [MUST]
      - Scenario: AC-030-01
    """
    await exercise_scenario(async_client, 'POST', '/auth/magic-link-request', 'MUST')


async def test_e2e_030_ac_030_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-030-02 [MUST]
      - Scenario: AC-030-02
    """
    await exercise_scenario(async_client, 'POST', '/auth/magic-link-verify', 'MUST')


async def test_e2e_030_ac_030_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-030-03 [MUST]
      - Scenario: AC-030-03
    """
    await exercise_scenario(async_client, 'POST', '/auth/magic-link-request', 'MUST')


async def test_e2e_030_ac_030_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-030-04 [MUST]
      - Scenario: AC-030-04
    """
    await exercise_scenario(async_client, 'POST', '/auth/magic-link-verify', 'MUST')


async def test_e2e_030_ac_030_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-030-05 [MUST NOT]
      - Scenario: AC-030-05
    """
    await exercise_scenario(async_client, 'POST', '/auth/magic-link-request', 'MUST NOT')


async def test_e2e_030_ac_030_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-030-06 [ALWAYS]
      - Scenario: AC-030-06
    """
    await exercise_scenario(async_client, 'POST', '/auth/magic-link-verify', 'ALWAYS')


async def test_e2e_030_ac_030_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-030-07 [CONCURRENCY]
      - Scenario: AC-030-07
    """
    await exercise_scenario(async_client, 'POST', '/auth/magic-link-request', 'CONCURRENCY')

