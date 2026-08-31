"""
E2E Test Suite for FEAT-020
Related Spec: docs/specs/SPEC-020-jovahagyasok-es-kontrollalt-valtoztatasok.md
Related Brief: briefs/BRIEF-020-jovahagyasok-es-kontrollalt-valtoztatasok.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_020_ac_020_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-01 [MUST]
      - Scenario: AC-020-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/approvals/pending', 'MUST')


async def test_e2e_020_ac_020_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-02 [MUST]
      - Scenario: AC-020-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/approvals/{id}/approve', 'MUST')


async def test_e2e_020_ac_020_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-03 [MUST]
      - Scenario: AC-020-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/approvals/{id}/reject', 'MUST')


async def test_e2e_020_ac_020_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-04 [MUST]
      - Scenario: AC-020-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/approvals/pending', 'MUST')


async def test_e2e_020_ac_020_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-05 [MUST]
      - Scenario: AC-020-05
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/approvals/{id}/approve', 'MUST')


async def test_e2e_020_ac_020_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-06 [MUST NOT]
      - Scenario: AC-020-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/approvals/{id}/reject', 'MUST NOT')


async def test_e2e_020_ac_020_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-07 [ALWAYS]
      - Scenario: AC-020-07
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/approvals/pending', 'ALWAYS')


async def test_e2e_020_ac_020_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-020-08 [CONCURRENCY]
      - Scenario: AC-020-08
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/approvals/{id}/approve', 'CONCURRENCY')


async def test_e2e_020_gui_flow():
    """
    Traceability:
      - Requirement: REQ-020-01 [MUST]
      - Scenario: AC-020-01
    """
    await browser_smoke('/')

