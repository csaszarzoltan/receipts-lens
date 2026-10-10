"""Webhook delivery must not reach internal addresses (SSRF).

The webhook URL is caller-supplied. Scheme and hostname checks alone let
literal private IPs such as ``http://127.0.0.1`` or ``http://10.0.0.5``
through, and validating a hostname's address and then connecting by name
lets a DNS answer change between the check and the connect (rebinding).
Delivery therefore connects to the exact address it validated.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from app import api, ssrf_guard


@pytest.fixture
def sent(monkeypatch):
    """Record every request the webhook client would send, without a socket."""
    requests: list[httpx.Request] = []

    async def _send(self, request, **kwargs):
        requests.append(request)
        return httpx.Response(200, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "send", _send)
    return requests


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8000/hook",
        "http://10.0.0.5/hook",
        "http://192.168.1.10/hook",
        "http://[::1]/hook",
    ],
)
@pytest.mark.test_id("TEST-RL-V02-195")
@pytest.mark.requirements("FEAT-RL-V02-REQ-063")
@pytest.mark.scenario("AC-RL-V02-44")
def test_webhook_to_internal_literal_ip_is_not_sent(url, sent):
    asyncio.run(api._deliver_webhook(url, {"job_id": "j1", "status": "failed"}))
    assert sent == []


@pytest.mark.test_id("TEST-RL-V02-196")
@pytest.mark.requirements("FEAT-RL-V02-REQ-063")
@pytest.mark.scenario("AC-RL-V02-44")
def test_webhook_whose_hostname_resolves_to_private_ip_is_not_sent(monkeypatch, sent):
    monkeypatch.setattr(ssrf_guard, "_resolve_addresses", lambda host: ["10.1.2.3"])
    asyncio.run(api._deliver_webhook("https://hooks.example.test/x", {"job_id": "j2"}))
    assert sent == []


@pytest.mark.test_id("TEST-RL-V02-197")
@pytest.mark.requirements("FEAT-RL-V02-REQ-063")
@pytest.mark.scenario("AC-RL-V02-44")
def test_webhook_connects_to_the_validated_address_only(monkeypatch, sent):
    """DNS rebinding guard: resolve once, then connect to that exact IP."""
    lookups: list[str] = []

    def _resolve(host):
        lookups.append(host)
        return ["93.184.216.34"]

    monkeypatch.setattr(ssrf_guard, "_resolve_addresses", _resolve)
    asyncio.run(api._deliver_webhook("https://hooks.example.test/x", {"job_id": "j3"}))

    assert len(lookups) == 1, "the hostname must not be resolved again at connect time"
    assert len(sent) == 1
    request = sent[0]
    assert request.url.host == "93.184.216.34"
    assert request.headers["host"] == "hooks.example.test"
    assert request.extensions["sni_hostname"] == "hooks.example.test"
    assert request.method == "POST"
