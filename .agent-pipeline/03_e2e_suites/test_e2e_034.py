"""
E2E Test Suite for FEAT-034
Related Spec: docs/specs/SPEC-034-e-mailben-erkezo-nyugtak-fogadasa.md
Related Brief: briefs/BRIEF-034-e-mailben-erkezo-nyugtak-fogadasa.md
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from blackbox_runtime import BASE_API_URL, BASE_WEB_URL, browser_smoke, exercise_scenario

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]


async def test_e2e_034_ac_034_01(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-01 [MUST]
      - Scenario: AC-034-01
    """
    await exercise_scenario(async_client, 'GET', '/product/inbound-emails', 'MUST')


async def test_e2e_034_ac_034_02(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-02 [MUST]
      - Scenario: AC-034-02
    """
    await exercise_scenario(async_client, 'POST', '/product/inbound-emails', 'MUST')


async def test_e2e_034_ac_034_03(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-03 [MUST]
      - Scenario: AC-034-03
    """
    await exercise_scenario(async_client, 'GET', '/product/inbound-emails/{email_id}', 'MUST')


async def test_e2e_034_ac_034_04(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-04 [MUST]
      - Scenario: AC-034-04
    """
    await exercise_scenario(async_client, 'POST', '/product/inbound-emails/{email_id}/attachments/{attachment_id}/retry', 'MUST')


async def test_e2e_034_ac_034_05(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-05 [MUST]
      - Scenario: AC-034-05
    """
    await exercise_scenario(async_client, 'GET', '/product/inbound-emails', 'MUST')


async def test_e2e_034_ac_034_06(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-06 [MUST NOT]
      - Scenario: AC-034-06
    """
    await exercise_scenario(async_client, 'POST', '/product/inbound-emails', 'MUST NOT')


async def test_e2e_034_ac_034_07(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-07 [ALWAYS]
      - Scenario: AC-034-07
    """
    await exercise_scenario(async_client, 'GET', '/product/inbound-emails/{email_id}', 'ALWAYS')


async def test_e2e_034_ac_034_08(async_client: AsyncClient):
    """
    Traceability:
      - Requirement: REQ-034-08 [CONCURRENCY]
      - Scenario: AC-034-08
    """
    await exercise_scenario(async_client, 'POST', '/product/inbound-emails/{email_id}/attachments/{attachment_id}/retry', 'CONCURRENCY')

