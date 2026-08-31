"""
E2E Test Suite for FEAT-006
Related Spec: docs/specs/SPEC-006-nyugta-feltoltese-es-feldolgozasi-sor.md
Related Brief: briefs/BRIEF-006-nyugta-feltoltese-es-feldolgozasi-sor.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_006_ac_006_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-01 [MUST]
      - Scenario: AC-006-01
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/upload', 'MUST')


async def test_e2e_006_ac_006_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-02 [MUST]
      - Scenario: AC-006-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/upload-url', 'MUST')


async def test_e2e_006_ac_006_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-03 [MUST]
      - Scenario: AC-006-03
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/batch/upload', 'MUST')


async def test_e2e_006_ac_006_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-04 [MUST]
      - Scenario: AC-006-04
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/batch/{batch_id}/status', 'MUST')


async def test_e2e_006_ac_006_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-05 [MUST]
      - Scenario: AC-006-05
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/upload', 'MUST')


async def test_e2e_006_ac_006_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-06 [MUST]
      - Scenario: AC-006-06
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/upload-url', 'MUST')


async def test_e2e_006_ac_006_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-07 [MUST]
      - Scenario: AC-006-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/batch/upload', 'MUST')


async def test_e2e_006_ac_006_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-08 [MUST NOT]
      - Scenario: AC-006-08
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/batch/{batch_id}/status', 'MUST NOT')


async def test_e2e_006_ac_006_09(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-09 [ALWAYS]
      - Scenario: AC-006-09
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/upload', 'ALWAYS')


async def test_e2e_006_ac_006_10(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-006-10 [CONCURRENCY]
      - Scenario: AC-006-10
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/upload-url', 'CONCURRENCY')


async def test_e2e_006_gui_flow():
    """
    Traceability:
      - Requirement: REQ-006-01 [MUST]
      - Scenario: AC-006-01
    """
    await browser_smoke('/')

