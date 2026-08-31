"""
E2E Test Suite for FEAT-007
Related Spec: docs/specs/SPEC-007-ai-alapu-nyugtafelismeres-es-bizonytalansag.md
Related Brief: briefs/BRIEF-007-ai-alapu-nyugtafelismeres-es-bizonytalansag.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_007_ac_007_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-01 [MUST]
      - Scenario: AC-007-01
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/parse', 'MUST')


async def test_e2e_007_ac_007_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-02 [MUST]
      - Scenario: AC-007-02
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/vision-parse', 'MUST')


async def test_e2e_007_ac_007_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-03 [MUST]
      - Scenario: AC-007-03
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/receipts/{id}/ocr-result', 'MUST')


async def test_e2e_007_ac_007_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-04 [MUST]
      - Scenario: AC-007-04
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/parse', 'MUST')


async def test_e2e_007_ac_007_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-05 [MUST]
      - Scenario: AC-007-05
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/vision-parse', 'MUST')


async def test_e2e_007_ac_007_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-06 [MUST]
      - Scenario: AC-007-06
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/receipts/{id}/ocr-result', 'MUST')


async def test_e2e_007_ac_007_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-07 [MUST NOT]
      - Scenario: AC-007-07
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/parse', 'MUST NOT')


async def test_e2e_007_ac_007_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-08 [ALWAYS]
      - Scenario: AC-007-08
    """
    await exercise_scenario(async_client, 'POST', '/api/v1/receipts/vision-parse', 'ALWAYS')


async def test_e2e_007_ac_007_09(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-007-09 [CONCURRENCY]
      - Scenario: AC-007-09
    """
    await exercise_scenario(async_client, 'GET', '/api/v1/receipts/{id}/ocr-result', 'CONCURRENCY')

