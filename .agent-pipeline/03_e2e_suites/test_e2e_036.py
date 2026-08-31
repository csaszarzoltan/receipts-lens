"""
E2E Test Suite for FEAT-036
Related Spec: docs/specs/SPEC-036-penznemvaltas-es-atvaltasi-arfolyam-kezelese.md
Related Brief: briefs/BRIEF-036-penznemvaltas-es-atvaltasi-arfolyam-kezelese.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_036_ac_036_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-01 [MUST]
      - Scenario: AC-036-01
    """
    await exercise_scenario(async_client, 'POST', '/product/exchange-rates', 'MUST')


async def test_e2e_036_ac_036_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-02 [MUST]
      - Scenario: AC-036-02
    """
    await exercise_scenario(async_client, 'POST', '/product/currency/convert', 'MUST')


async def test_e2e_036_ac_036_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-03 [MUST]
      - Scenario: AC-036-03
    """
    await exercise_scenario(async_client, 'POST', '/product/exchange-rates', 'MUST')


async def test_e2e_036_ac_036_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-04 [MUST]
      - Scenario: AC-036-04
    """
    await exercise_scenario(async_client, 'POST', '/product/currency/convert', 'MUST')


async def test_e2e_036_ac_036_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-05 [MUST]
      - Scenario: AC-036-05
    """
    await exercise_scenario(async_client, 'POST', '/product/exchange-rates', 'MUST')


async def test_e2e_036_ac_036_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-06 [MUST NOT]
      - Scenario: AC-036-06
    """
    await exercise_scenario(async_client, 'POST', '/product/currency/convert', 'MUST NOT')


async def test_e2e_036_ac_036_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-07 [ALWAYS]
      - Scenario: AC-036-07
    """
    await exercise_scenario(async_client, 'POST', '/product/exchange-rates', 'ALWAYS')


async def test_e2e_036_ac_036_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-036-08 [CONCURRENCY]
      - Scenario: AC-036-08
    """
    await exercise_scenario(async_client, 'POST', '/product/currency/convert', 'CONCURRENCY')

