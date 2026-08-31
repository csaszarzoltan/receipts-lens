"""
E2E Test Suite for FEAT-016
Related Spec: docs/specs/SPEC-016-haztartasi-egyuttmukodes-es-csaladi-postafiok.md
Related Brief: briefs/BRIEF-016-haztartasi-egyuttmukodes-es-csaladi-postafiok.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_016_ac_016_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-01 [MUST]
      - Scenario: AC-016-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/inbox', 'MUST')


async def test_e2e_016_ac_016_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-02 [MUST]
      - Scenario: AC-016-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/inbox/upload', 'MUST')


async def test_e2e_016_ac_016_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-03 [MUST]
      - Scenario: AC-016-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/household/members', 'MUST')


async def test_e2e_016_ac_016_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-04 [MUST]
      - Scenario: AC-016-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/household/invite', 'MUST')


async def test_e2e_016_ac_016_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-05 [MUST]
      - Scenario: AC-016-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/inbox', 'MUST')


async def test_e2e_016_ac_016_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-06 [MUST]
      - Scenario: AC-016-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/inbox/upload', 'MUST')


async def test_e2e_016_ac_016_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-07 [MUST NOT]
      - Scenario: AC-016-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/household/members', 'MUST NOT')


async def test_e2e_016_ac_016_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-08 [ALWAYS]
      - Scenario: AC-016-08
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/household/invite', 'ALWAYS')


async def test_e2e_016_ac_016_09(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-016-09 [CONCURRENCY]
      - Scenario: AC-016-09
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/inbox', 'CONCURRENCY')


async def test_e2e_016_gui_flow():
    """
    Traceability:
      - Requirement: REQ-016-01 [MUST]
      - Scenario: AC-016-01
    """
    await browser_smoke('/')

