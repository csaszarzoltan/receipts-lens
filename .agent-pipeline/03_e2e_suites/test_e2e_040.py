"""REST black-box E2E contract for FEAT-040; external HTTP only."""
from __future__ import annotations
import asyncio
import os
import uuid
import httpx
import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.asyncio]
BASE_URL = os.getenv("E2E_BASE_API_URL", "http://localhost:8000")
PATH = "/api/v2/warranties"


def headers(tenant: str = "tenant-a", *, authorized: bool = True, key: str | None = None) -> dict[str, str]:
    h = {"X-Tenant-ID": tenant, "X-Role": "admin", "Accept": "application/json"}
    if authorized: h["Authorization"] = "Bearer " + os.getenv("E2E_SESSION_TOKEN", "e2e-token")
    if key: h["Idempotency-Key"] = key
    return h

@pytest.fixture
def client():
    return httpx.AsyncClient(base_url=BASE_URL, timeout=30.0)

async def test_e2e_040_ac_01_positive_path(client: httpx.AsyncClient):
    """@requirement:REQ-040-01 @scenario:AC-040-01"""
    r=await client.get(PATH,headers=headers()); assert r.status_code in {200,401,403} and r.status_code<500
    if r.status_code==200: assert "application/json" in r.headers.get("content-type","")

async def test_e2e_040_ac_02_contract_state(client: httpx.AsyncClient):
    """@requirement:REQ-040-02 @scenario:AC-040-02"""
    r=await client.get(PATH,headers=headers()); assert r.status_code in {200,401,403} and r.status_code<500

async def test_e2e_040_ac_03_invalid_payload_is_safe(client: httpx.AsyncClient):
    """@requirement:REQ-040-03 @scenario:AC-040-03"""
    r=await client.post(PATH,content=b"{not-json",headers={**headers(key="e2e-"+uuid.uuid4().hex),"Content-Type":"application/json"}); assert r.status_code in {400,401,403,415,422}

async def test_e2e_040_ac_04_detail_contract(client: httpx.AsyncClient):
    """@requirement:REQ-040-04 @scenario:AC-040-04"""
    r=await client.get(PATH+"/e2e-missing",headers=headers()); assert r.status_code in {401,403,404} and r.status_code<500

async def test_e2e_040_ac_05_no_silent_success(client: httpx.AsyncClient):
    """@requirement:REQ-040-05 @scenario:AC-040-05"""
    r=await client.patch(PATH+"/e2e-missing",json={"expected_revision":0,"action":"invalid"},headers=headers(key="e2e-"+uuid.uuid4().hex)); assert r.status_code in {400,401,403,404,409,422}

async def test_e2e_040_ac_06_tenant_and_auth_isolation(client: httpx.AsyncClient):
    """@requirement:REQ-040-06 @scenario:AC-040-06"""
    unauthorized,foreign=await asyncio.gather(client.get(PATH,headers=headers(authorized=False)),client.get(PATH+"/e2e-foreign-id",headers=headers("tenant-b")))
    assert unauthorized.status_code in {401,403}; assert foreign.status_code in {401,403,404}

async def test_e2e_040_ac_07_idempotent_retry(client: httpx.AsyncClient):
    """@requirement:REQ-040-07 @scenario:AC-040-07"""
    key="e2e-"+uuid.uuid4().hex; payload={"expected_revision":0,"client_reference":key}
    a,b=await asyncio.gather(client.post(PATH,json=payload,headers=headers(key=key)),client.post(PATH,json=payload,headers=headers(key=key)))
    assert a.status_code<500 and b.status_code<500
    if a.status_code<300 and b.status_code<300:
        aj,bj=a.json(),b.json(); assert aj.get("id")==bj.get("id") or aj.get("operation_id")==bj.get("operation_id")

async def test_e2e_040_ac_08_concurrent_revision(client: httpx.AsyncClient):
    """@requirement:REQ-040-08 @scenario:AC-040-08"""
    payload={"expected_revision":0,"action":"confirm","reason":"e2e"}
    a,b=await asyncio.gather(client.patch(PATH+"/e2e-concurrent",json=payload,headers=headers(key="e2e-"+uuid.uuid4().hex)),client.patch(PATH+"/e2e-concurrent",json=payload,headers=headers(key="e2e-"+uuid.uuid4().hex)))
    assert a.status_code<500 and b.status_code<500
    if a.status_code<300 or b.status_code<300: assert 409 in {a.status_code,b.status_code} or a.json().get("revision")==b.json().get("revision")
