"""
E2E Test Suite for FEAT-009
Related Spec: docs/specs/SPEC-009-nyugtaellenorzes-es-javitas.md
Related Brief: briefs/BRIEF-009-nyugtaellenorzes-es-javitas.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_009_ac_009_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-01 [MUST]
      - Scenario: AC-009-01
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/review/pending', 'MUST')


async def test_e2e_009_ac_009_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-02 [MUST]
      - Scenario: AC-009-02
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/receipts/{id}/correct', 'MUST')


async def test_e2e_009_ac_009_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-03 [MUST]
      - Scenario: AC-009-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/receipts/{id}/confirm', 'MUST')


async def test_e2e_009_ac_009_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-04 [MUST]
      - Scenario: AC-009-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/receipts/{id}/reject', 'MUST')


async def test_e2e_009_ac_009_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-05 [MUST]
      - Scenario: AC-009-05
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/review/pending', 'MUST')


async def test_e2e_009_ac_009_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-06 [MUST]
      - Scenario: AC-009-06
    """
    await exercise_scenario(async_client, 'PUT', '/api/v2/receipts/{id}/correct', 'MUST')


async def test_e2e_009_ac_009_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-07 [MUST NOT]
      - Scenario: AC-009-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/receipts/{id}/confirm', 'MUST NOT')


async def test_e2e_009_ac_009_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-08 [ALWAYS]
      - Scenario: AC-009-08
    """
    await exercise_scenario(async_client, 'POST', '/api/v2/receipts/{id}/reject', 'ALWAYS')


async def test_e2e_009_ac_009_09(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-009-09 [CONCURRENCY]
      - Scenario: AC-009-09
    """
    await exercise_scenario(async_client, 'GET', '/api/v2/review/pending', 'CONCURRENCY')


async def test_e2e_009_gui_flow():
    """
    Traceability:
      - Requirement: REQ-009-01 [MUST]
      - Scenario: AC-009-01
    """
    await browser_smoke('/')

