"""
E2E Test Suite for FEAT-037
Related Spec: docs/specs/SPEC-037-diagnosztikai-csomag-es-tamogatasi-hibaelemzes.md
Related Brief: briefs/BRIEF-037-diagnosztikai-csomag-es-tamogatasi-hibaelemzes.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_037_ac_037_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-01 [MUST]
      - Scenario: AC-037-01
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics', 'MUST')


async def test_e2e_037_ac_037_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-02 [MUST]
      - Scenario: AC-037-02
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics/bundle', 'MUST')


async def test_e2e_037_ac_037_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-03 [MUST]
      - Scenario: AC-037-03
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics', 'MUST')


async def test_e2e_037_ac_037_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-04 [MUST]
      - Scenario: AC-037-04
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics/bundle', 'MUST')


async def test_e2e_037_ac_037_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-05 [MUST]
      - Scenario: AC-037-05
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics', 'MUST')


async def test_e2e_037_ac_037_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-06 [MUST NOT]
      - Scenario: AC-037-06
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics/bundle', 'MUST NOT')


async def test_e2e_037_ac_037_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-07 [ALWAYS]
      - Scenario: AC-037-07
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics', 'ALWAYS')


async def test_e2e_037_ac_037_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-037-08 [CONCURRENCY]
      - Scenario: AC-037-08
    """
    await exercise_scenario(async_client, 'GET', '/product/diagnostics/bundle', 'CONCURRENCY')

