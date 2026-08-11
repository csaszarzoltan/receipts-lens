"""Live QBO OAuth callback, refresh and revoke completion tests.

These cover the missing pieces called out in US-010/011/012 (live
code->token exchange, expiry-aware refresh rotation, and Intuit revoke
on disconnect). Intuit HTTP is mocked at the transport level so the
tests run hermetically; the OAuth client still hits its fixed Intuit
hosts (verified by recording request URLs).
"""
import base64
import json
import os
from datetime import UTC, datetime, timedelta

import httpx
from fastapi.testclient import TestClient

os.environ['RECEIPTLENS_CREDENTIAL_KEY'] = base64.urlsafe_b64encode(b'v' * 32).decode()
os.environ['RECEIPTLENS_QBO_CLIENT_ID'] = 'intuit-app-123'
os.environ['RECEIPTLENS_QBO_CLIENT_SECRET'] = 'secret-value'

from app.api import app
from app.connection_service import ConnectionService
from app.credential_store import CredentialStore
from app.intuit_oauth import TOKEN_URL, IntuitOAuthClient
from app.product_service import ProductService

H = {'X-Tenant-ID': 'live-qbo', 'X-Role': 'admin'}

TOKENS = {
    'access_token': 'access-live',
    'refresh_token': 'refresh-live',
    'expires_in': 3600,
    'x_refresh_token_expires_in': 8726400,
}


class _Recorder:
    """httpx transport that records requests and answers OAuth calls."""

    def __init__(self):
        self.requests = []
        self.exchange_status = 200
        self.exchange_body = TOKENS
        self.refresh_status = 200
        self.refresh_body = {**TOKENS, 'access_token': 'access-refreshed', 'refresh_token': 'refresh-new'}
        self.revoke_status = 200

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append((request.method, str(request.url), request.content.decode('utf-8', 'replace')))
        if str(request.url).startswith(TOKEN_URL):
            if 'grant_type=authorization_code' in request.content.decode():
                status, body = self.exchange_status, self.exchange_body
            else:
                status, body = self.refresh_status, self.refresh_body
            return httpx.Response(status, json=body, request=request)
        if 'revoke' in str(request.url):
            return httpx.Response(self.revoke_status, json={}, request=request)
        return httpx.Response(404, json={}, request=request)


def _recorder_client(rec: _Recorder) -> IntuitOAuthClient:
    return IntuitOAuthClient(
        client_id='intuit-app-123',
        client_secret='secret-value',
        redirect_uri='/product/connections/quickbooks/oauth/callback',
        client=httpx.Client(transport=httpx.MockTransport(rec.handle_request)),
    )


def _service(rec: _Recorder | None = None) -> tuple[ProductService, ConnectionService, _Recorder]:
    import tempfile
    tmp = tempfile.mkdtemp()
    service = ProductService(os.path.join(tmp, 'db.sqlite'))
    rec = rec or _Recorder()
    cs = ConnectionService(service, CredentialStore(), oauth=_recorder_client(rec))
    return service, cs, rec


def _complete(service: ProductService, cs: ConnectionService) -> str:
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    conn = cs.complete_oauth(actor, started['state'], 'code-1', 'realm-1', TOKENS)
    return conn['connection_id']


def test_callback_route_exchanges_code_and_persists_connection():
    """The live callback route performs the real code->token exchange."""
    rec = _Recorder()
    _, cs, rec = _service(rec)
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')

    # Point the app-level _connections() at our service so the route uses it.
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(
            f'/product/connections/quickbooks/oauth/callback?state={started["state"]}&code=the-code&realmId=realm-42',
            headers=H,
        )
    finally:
        pa._connections = orig
    assert r.status_code == 201, r.text
    assert r.json()['status'] == 'connected'
    assert r.json()['redirect'] == '/integrations'
    # The exchange hit Intuit's fixed token endpoint with the authorization
    # code and the PKCE verifier stored at start_oauth time.
    exchange = [b for m, u, b in rec.requests if m == 'POST' and u.startswith(TOKEN_URL) and 'code=the-code' in b]
    assert exchange, 'expected an Intuit token exchange'
    assert 'code_verifier=' in exchange[0], 'PKCE verifier must be sent with the exchange'
    # The authorization URL carried a real S256 challenge (not just the method).
    auth_url = started['authorization_url']
    assert 'code_challenge=' in auth_url, 'authorization URL must carry a PKCE challenge'
    challenge = auth_url.split('code_challenge=')[1].split('&')[0]
    assert challenge not in ('', 'configured')
    # A provider connection now exists for the tenant.
    conns = cs.list_connections(actor)
    assert len(conns) == 1
    assert conns[0]['provider_company_id'] == 'realm-42'
    assert conns[0]['health'] == 'healthy'
    # No token material is returned or leaked into the response.
    assert 'access-live' not in r.text


def test_callback_rejects_unknown_state():
    """A state that was never issued (or already consumed) is rejected."""
    _, cs, _ = _service()
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(
            '/product/connections/quickbooks/oauth/callback?state=unknown-state-123&code=c&realmId=realm-1',
            headers=H,
        )
    finally:
        pa._connections = orig
    assert r.status_code == 422
    assert r.json()['detail']['code'] == 'oauth_state_invalid'
    assert cs.list_connections(type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()) == []


def test_callback_requires_realm():
    _, cs, _ = _service()
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(
            '/product/connections/quickbooks/oauth/callback?state=some-state-value&code=c&realmId=',
            headers=H,
        )
    finally:
        pa._connections = orig
    assert r.status_code == 422


def test_callback_accepts_browser_get_redirect():
    """Intuit redirects the browser with GET; the route must accept it."""
    rec = _Recorder()
    _, cs, rec = _service(rec)
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).get(
            f'/product/connections/quickbooks/oauth/callback?state={started["state"]}&code=the-code&realmId=realm-42',
            headers=H,
        )
    finally:
        pa._connections = orig
    assert r.status_code == 201, r.text
    assert r.json()['status'] == 'connected'
    # The exchange ran over GET too.
    assert any(m == 'POST' and u.startswith(TOKEN_URL) and 'code=the-code' in b for m, u, b in rec.requests)


def test_refresh_route_rotates_expired_token():
    """An expiring credential is rotated via Intuit and the DB is updated."""
    rec = _Recorder()
    _, cs, rec = _service(rec)
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    # Store with an already-expired expiry.
    conn = cs.complete_oauth(actor, started['state'], 'c', 'realm-1', {**TOKENS, 'expires_in': -100})

    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(f'/product/connections/{conn["connection_id"]}/refresh', headers=H)
    finally:
        pa._connections = orig
    assert r.status_code == 200, r.text
    assert r.json()['status'] == 'refreshed'
    assert any('grant_type=refresh_token' in b for _, u, b in rec.requests)
    # Stored tokens rotated (encrypted) — verify via the service.
    tokens, refreshed = cs.refresh_if_needed(actor, conn['connection_id'])
    assert refreshed is False  # already fresh now
    assert tokens['access_token'] == 'access-refreshed'


def test_refresh_not_needed_when_fresh():
    _, cs, _ = _service()
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    conn = cs.complete_oauth(actor, started['state'], 'c', 'realm-1', TOKENS)
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(f'/product/connections/{conn["connection_id"]}/refresh', headers=H)
    finally:
        pa._connections = orig
    assert r.status_code == 200
    assert r.json()['status'] == 'not_needed'


def test_disconnect_revokes_at_intuit():
    """Disconnect performs a best-effort Intuit revoke with the refresh token."""
    rec = _Recorder()
    _, cs, rec = _service(rec)
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    conn = cs.complete_oauth(actor, started['state'], 'c', 'realm-1', TOKENS)
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(f'/product/connections/{conn["connection_id"]}/disconnect', headers=H)
    finally:
        pa._connections = orig
    assert r.status_code == 200
    assert r.json()['health'] == 'disconnected'
    # The revoke call carried the refresh token to the fixed revoke host.
    revoke_calls = [b for _, u, b in rec.requests if 'revoke' in u]
    assert revoke_calls, 'expected an Intuit revoke call'
    assert 'refresh-live' in revoke_calls[0]


def test_disconnect_succeeds_when_revoke_fails():
    """Revoke failure must not break local disconnect."""
    rec = _Recorder()
    rec.revoke_status = 500
    _, cs, rec = _service(rec)
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    conn = cs.complete_oauth(actor, started['state'], 'c', 'realm-1', TOKENS)
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(f'/product/connections/{conn["connection_id"]}/disconnect', headers=H)
    finally:
        pa._connections = orig
    assert r.status_code == 200
    assert r.json()['health'] == 'disconnected'


def test_exchange_failure_is_502_without_leaking_credentials():
    rec = _Recorder()
    rec.exchange_status = 400
    rec.exchange_body = {'error': 'invalid_grant'}
    _, cs, rec = _service(rec)
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(
            f'/product/connections/quickbooks/oauth/callback?state={started["state"]}&code=bad&realmId=realm-1',
            headers=H,
        )
    finally:
        pa._connections = orig
    assert r.status_code == 502
    assert 'invalid_grant' in r.json()['detail']['message']
    assert 'secret-value' not in r.text
    assert 'access-live' not in r.text


def test_complete_oauth_callback_derives_tenant_from_state():
    """complete_oauth_callback() must not require tenant headers."""
    _, cs, _rec = _service()
    actor = type('A', (), {'tenant_id': 'state-tenant', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    conn = cs.complete_oauth_callback(started['state'], 'code', 'realm-x', TOKENS)
    assert conn['tenant_id'] == 'state-tenant'
    # State is single-use: a second completion must fail.
    try:
        cs.complete_oauth_callback(started['state'], 'code', 'realm-x', TOKENS)
        raise AssertionError('expected ValueError on reuse')
    except ValueError as exc:
        assert str(exc) == 'oauth_state_invalid'


def test_refresh_failure_marks_reauthorization_and_returns_409():
    rec = _Recorder()
    rec.refresh_status = 400
    rec.refresh_body = {'error': 'invalid_grant'}
    _, cs, rec = _service(rec)
    actor = type('A', (), {'tenant_id': 'live-qbo', 'role': 'admin'})()
    started = cs.start_oauth(actor, '/integrations')
    conn = cs.complete_oauth(actor, started['state'], 'c', 'realm-1', {**TOKENS, 'expires_in': -100})
    import app.product_api as pa
    orig = pa._connections
    pa._connections = lambda: cs
    try:
        r = TestClient(app).post(f'/product/connections/{conn["connection_id"]}/refresh', headers=H)
    finally:
        pa._connections = orig
    assert r.status_code == 409
    assert r.json()['detail']['code'] == 'reauthorization_required'
    # Health flipped so the UI prompts for reconnect.
    assert cs.get(actor, conn['connection_id'])['reauthorization_required'] is True
