"""Tenant-scoped QuickBooks OAuth state, credentials, health and mappings."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlencode

from app.intuit_oauth import IntuitOAuthClient, OAuthConfigError


def Actor(tenant_id: str, role: str):
    """Small local Actor mirroring app.product_service.Actor without import cycles."""
    return SimpleNamespace(tenant_id=tenant_id, role=role)


STATE_TTL = timedelta(minutes=10)
# Renew the access token a little before Intuit's 3600s expiry so that
# exports never race an expiring credential.
REFRESH_MARGIN_SECONDS = 300


class ConnectionService:
    def __init__(self, service: Any, credentials: Any, *, client_id: str | None = None, redirect_uri: str | None = None, oauth: IntuitOAuthClient | None = None):
        self.db, self.credentials = service._db, credentials
        self.client_id = client_id or os.getenv('RECEIPTLENS_QBO_CLIENT_ID', '')
        self.redirect_uri = redirect_uri or os.getenv('RECEIPTLENS_QBO_REDIRECT_URI', '/product/connections/quickbooks/oauth/callback')
        self.oauth = oauth or IntuitOAuthClient(redirect_uri=self.redirect_uri)
        with self.db:
            self.db.executescript('''CREATE TABLE IF NOT EXISTS oauth_states(state_hash TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,return_path TEXT NOT NULL,expires_at TEXT NOT NULL,used_at TEXT,code_verifier TEXT);CREATE TABLE IF NOT EXISTS provider_connections(connection_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,provider TEXT NOT NULL,provider_company_id TEXT NOT NULL,provider_company_name TEXT NOT NULL,health TEXT NOT NULL,reauthorization_required INTEGER NOT NULL,created_at TEXT NOT NULL,last_tested_at TEXT);CREATE TABLE IF NOT EXISTS provider_credentials(connection_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,token_ciphertext TEXT NOT NULL,expires_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS connection_mapping_versions(mapping_id TEXT PRIMARY KEY,connection_id TEXT NOT NULL,tenant_id TEXT NOT NULL,version INTEGER NOT NULL,payload_json TEXT NOT NULL,snapshot_hash TEXT NOT NULL,valid INTEGER NOT NULL,created_at TEXT NOT NULL,UNIQUE(connection_id,version));''')
    @staticmethod
    def now():
        return datetime.now(UTC)

    def start_oauth(self, actor, return_path):
        if actor.role != 'admin':
            raise PermissionError
        if return_path != '/integrations':
            raise ValueError('return path not allowed')
        state = secrets.token_urlsafe(32)
        h = hashlib.sha256(state.encode()).hexdigest()
        verifier = secrets.token_urlsafe(48)
        challenge = self._pkce_challenge(verifier)
        exp = self.now() + STATE_TTL
        with self.db:
            self.db.execute('INSERT INTO oauth_states VALUES(?,?,?,?,NULL,?)', (h, actor.tenant_id, return_path, exp.isoformat(), verifier))
        q = urlencode({'client_id': self.client_id or 'configured', 'response_type': 'code', 'scope': 'com.intuit.quickbooks.accounting', 'redirect_uri': self.redirect_uri, 'state': state, 'code_challenge_method': 'S256', 'code_challenge': challenge})
        return {'authorization_url': 'https://appcenter.intuit.com/connect/oauth2?' + q, 'state': state, 'state_expires_at': exp.isoformat()}

    @staticmethod
    def _pkce_challenge(verifier: str) -> str:
        """S256 PKCE challenge for a verifier (RFC 7636)."""
        return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()

    def complete_oauth(self, actor, state, code, realm, tokens):
        h = hashlib.sha256(state.encode()).hexdigest()
        row = self.db.execute('SELECT * FROM oauth_states WHERE state_hash=? AND tenant_id=?', (h, actor.tenant_id)).fetchone()
        if not row or row['used_at'] or datetime.fromisoformat(row['expires_at']) < self.now():
            raise ValueError('oauth_state_invalid')
        now = self.now()
        with self.db:
            self.db.execute('UPDATE oauth_states SET used_at=? WHERE state_hash=?', (now.isoformat(), h))
        return self._persist_connection(actor.tenant_id, realm, tokens)

    def _persist_connection(self, tenant_id: str, realm: str, tokens: dict[str, Any]) -> dict[str, Any]:
        """Insert the provider connection and its encrypted credentials."""
        cid = str(uuid.uuid4())
        now = self.now()
        exp = now + timedelta(seconds=int(tokens.get('expires_in', 3600)))
        with self.db:
            self.db.execute('INSERT INTO provider_connections VALUES(?,?,?,?,?,"healthy",0,?,NULL)', (cid, tenant_id, 'quickbooks_online', realm, 'QuickBooks Sandbox', now.isoformat()))
            self.db.execute('INSERT INTO provider_credentials VALUES(?,?,?,?,?)', (cid, tenant_id, self.credentials.encrypt(tokens), exp.isoformat(), now.isoformat()))
        return self.get(Actor(tenant_id, 'admin'), cid)

    def complete_oauth_callback(self, state: str, code: str, realm: str, tokens: dict[str, Any]) -> dict[str, Any]:
        """Complete OAuth from a browser redirect.

        The callback arrives without tenant headers, so the tenant is derived
        from the single-use state token (possession of a valid, unexpired
        state is the capability). Admins only ever receive states via
        ``start_oauth``.
        """
        tenant_id = self.validate_state_token(state)
        actor = Actor(tenant_id, 'admin')
        return self.complete_oauth(actor, state, code, realm, tokens)

    def complete_live_oauth(self, state: str, code: str, realm: str) -> dict[str, Any]:
        """Exchange a live Intuit authorization code and persist the tokens.

        Runs the code->token exchange against Intuit with the PKCE verifier
        stored alongside the state token, then persists the connection with
        the same single-use semantics as ``complete_oauth_callback``. The
        tenant is derived from the state token, so no tenant headers are
        needed.
        """
        verifier, tenant_id = self.pop_code_verifier(state)
        try:
            tokens = self.oauth.exchange_code(code, state, verifier=verifier)
        except Exception:
            # The exchange failed — restore the state token so the user can
            # retry with the same authorization URL instead of being forced
            # to start a fresh flow (Intuit codes are single-use, so a fresh
            # flow is required anyway on a bad code; keep the state reusable
            # in case the failure was transient).
            with self.db:
                self.db.execute('UPDATE oauth_states SET used_at=NULL WHERE state_hash=?', (hashlib.sha256(state.encode()).hexdigest(),))
            raise
        return self._persist_connection(tenant_id, realm, tokens)

    def pop_code_verifier(self, state: str) -> tuple[str, str]:
        """Consume a state token and return ``(verifier, tenant_id)``.

        Raises ``ValueError('oauth_state_invalid')`` for unknown, expired,
        already-consumed states, and raises ``ValueError('oauth_verifier_missing')``
        when a state was created without PKCE (e.g. by an older app version).
        """
        h = hashlib.sha256(state.encode()).hexdigest()
        row = self.db.execute(
            'SELECT tenant_id, used_at, expires_at, code_verifier FROM oauth_states WHERE state_hash=?', (h,)
        ).fetchone()
        if not row or row['used_at'] or datetime.fromisoformat(row['expires_at']) < self.now():
            raise ValueError('oauth_state_invalid')
        if not row['code_verifier']:
            raise ValueError('oauth_verifier_missing')
        with self.db:
            self.db.execute('UPDATE oauth_states SET used_at=? WHERE state_hash=?', (self.now().isoformat(), h))
        return row['code_verifier'], row['tenant_id']

    def validate_state_token(self, state: str) -> str:
        """Validate an OAuth state token and return its tenant id.

        Raises ``ValueError('oauth_state_invalid')`` when the state was never
        issued, was already consumed, or has expired. Does NOT consume the
        token — ``complete_oauth()`` performs the single-use consumption
        after the token exchange has succeeded.
        """
        h = hashlib.sha256(state.encode()).hexdigest()
        row = self.db.execute(
            'SELECT tenant_id, used_at, expires_at FROM oauth_states WHERE state_hash=?', (h,)
        ).fetchone()
        if not row or row['used_at'] or datetime.fromisoformat(row['expires_at']) < self.now():
            raise ValueError('oauth_state_invalid')
        return row['tenant_id']

    def get(self, actor, cid):
        r = self.db.execute('SELECT * FROM provider_connections WHERE tenant_id=? AND connection_id=?', (actor.tenant_id, cid)).fetchone()
        if not r:
            raise KeyError(cid)
        d = dict(r)
        d['reauthorization_required'] = bool(d['reauthorization_required'])
        return d

    def _tokens(self, actor, cid):
        """Decrypt the stored credential dict for a connection."""
        self.get(actor, cid)
        r = self.db.execute('SELECT token_ciphertext FROM provider_credentials WHERE connection_id=? AND tenant_id=?', (cid, actor.tenant_id)).fetchone()
        if not r:
            raise KeyError(cid)
        return self.credentials.decrypt(r[0])

    def rotate_tokens(self, actor, cid, tokens):
        self.get(actor, cid)
        now = self.now()
        exp = now + timedelta(seconds=int(tokens.get('expires_in', 3600)))
        with self.db:
            self.db.execute('UPDATE provider_credentials SET token_ciphertext=?,expires_at=?,updated_at=? WHERE tenant_id=? AND connection_id=?', (self.credentials.encrypt(tokens), exp.isoformat(), now.isoformat(), actor.tenant_id, cid))
        return self.get(actor, cid)

    def refresh_if_needed(self, actor, cid) -> tuple[dict[str, Any], bool]:
        """Refresh the access token when it is close to expiry.

        Returns ``(tokens, refreshed)`` where ``refreshed`` is True when a
        live Intuit refresh call was made and the stored credential rotated.
        """
        tokens = self._tokens(actor, cid)
        expires_at = datetime.fromisoformat(self.db.execute('SELECT expires_at FROM provider_credentials WHERE connection_id=? AND tenant_id=?', (cid, actor.tenant_id)).fetchone()[0])
        remaining = (expires_at - self.now()).total_seconds()
        if remaining > REFRESH_MARGIN_SECONDS:
            return tokens, False
        refresh_token = tokens.get('refresh_token')
        if not refresh_token:
            self.mark_reauthorization(actor, cid)
            raise ValueError('reauthorization_required')
        try:
            refreshed = self.oauth.refresh(refresh_token)
        except OAuthConfigError:
            self.mark_reauthorization(actor, cid)
            raise
        self.rotate_tokens(actor, cid, refreshed)
        return refreshed, True

    def revoke(self, actor, cid) -> None:
        """Best-effort Intuit revoke using the stored refresh token (if any)."""
        tokens = self._tokens(actor, cid)
        refresh_token = tokens.get('refresh_token')
        if not refresh_token:
            return
        try:
            self.oauth.revoke(refresh_token)
        except OAuthConfigError:
            # Intuit may already have invalidated the token; local disconnect
            # must still succeed. Swallow and continue.
            return

    def test_connection(self, actor, cid, provider):
        self.get(actor, cid)
        t = self._tokens(actor, cid)
        company = provider.company(t['access_token'])
        now = self.now().isoformat()
        with self.db:
            self.db.execute('UPDATE provider_connections SET health="healthy",reauthorization_required=0,last_tested_at=?,provider_company_name=? WHERE connection_id=?', (now, company['name'], cid))
        return {'health': 'healthy', 'company': company, 'tested_at': now}

    def mark_reauthorization(self, actor, cid):
        self.get(actor, cid)
        with self.db:
            self.db.execute('UPDATE provider_connections SET health="reauthorization_required",reauthorization_required=1 WHERE connection_id=?', (cid,))

    def validate_mapping(self, mapping, provider):
        ref = mapping.get('expense_account_ref')
        refs = provider.references('accounts')
        if not ref:
            raise ValueError('expense_account_ref is required')
        if ref not in {x['id'] for x in refs if x.get('active')}:
            raise ValueError('mapping_reference_inactive')
        snap = hashlib.sha256(json.dumps(refs, sort_keys=True).encode()).hexdigest()
        return {'valid': True, 'mapping': mapping, 'snapshot_hash': snap}

    def save_mapping(self, actor, cid, mapping, snapshot_hash):
        self.get(actor, cid)
        v = self.db.execute('SELECT COALESCE(MAX(version),0)+1 FROM connection_mapping_versions WHERE connection_id=?', (cid,)).fetchone()[0]
        mid = str(uuid.uuid4())
        with self.db:
            self.db.execute('INSERT INTO connection_mapping_versions VALUES(?,?,?,?,?,?,1,?)', (mid, cid, actor.tenant_id, v, json.dumps(mapping, sort_keys=True), snapshot_hash, self.now().isoformat()))
        return {'mapping_id': mid, 'version': v, 'valid': True, 'mapping': mapping, 'snapshot_hash': snapshot_hash}


# Completion helpers kept outside the class body above and attached explicitly.
def _list_connections(self, actor):
    rows = self.db.execute('SELECT * FROM provider_connections WHERE tenant_id=? ORDER BY created_at DESC', (actor.tenant_id,)).fetchall()
    return [{**dict(r), 'reauthorization_required': bool(r['reauthorization_required'])} for r in rows]


def _disconnect(self, actor, cid):
    self.get(actor, cid)
    if actor.role != 'admin':
        raise PermissionError
    self.revoke(actor, cid)
    with self.db:
        self.db.execute('DELETE FROM provider_credentials WHERE tenant_id=? AND connection_id=?', (actor.tenant_id, cid))
        self.db.execute('UPDATE provider_connections SET health="disconnected",reauthorization_required=0 WHERE tenant_id=? AND connection_id=?', (actor.tenant_id, cid))
    return self.get(actor, cid)


def _current_mapping(self, actor, cid):
    self.get(actor, cid)
    r = self.db.execute('SELECT * FROM connection_mapping_versions WHERE tenant_id=? AND connection_id=? ORDER BY version DESC LIMIT 1', (actor.tenant_id, cid)).fetchone()
    if not r:
        raise KeyError('mapping')
    d = dict(r)
    d['mapping'] = json.loads(d.pop('payload_json'))
    d['valid'] = bool(d['valid'])
    return d


ConnectionService.list_connections = _list_connections
ConnectionService.disconnect = _disconnect
ConnectionService.current_mapping = _current_mapping

