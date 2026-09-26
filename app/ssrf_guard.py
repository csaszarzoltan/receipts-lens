"""SSRF guard for user-supplied image URL fetching."""

from __future__ import annotations

import ipaddress
import logging
import socket
import urllib.parse
from collections.abc import Iterable as IterableType
from collections.abc import Iterator

import httpx
from fastapi import HTTPException
import time

from app.ssrf_address import (  # noqa: F401 - a publikus nevek re-exportja
    _RESERVED_NETWORKS,
    _DEFAULT_TOTAL_TIMEOUT,
    _BLOCKED_HOSTNAME_SUBSTRINGS,
    _BLOCKED_HOSTNAME_EXACT,
    _is_reserved,
    _deadline_expired,
    _verify_peer_ip,
    _resolve_with_deadline,
    _reject_compressed_response,
    _is_blocked_host,
)

logger = logging.getLogger(__name__)

_DEFAULT_MAX_BYTES = 20_000_000
_DEFAULT_TIMEOUT = 30.0

_ALLOWED_SCHEMES = ("http", "https")



















def _verify_actual_peer(request: object, response: object) -> None:
    """A kapcsolat tényleges peer IP-jét ellenőrli; hiányában fail-closed.

    Az ``httpx`` a peer címet a ``network_stream`` extensionben adja át. Ha
    nincs meg (teszt-mock vagy nem-socket transport), a kérésben validált
    címeket ellenőrizzük újra — a védelem így is aktív marad.
    """
    stream = (getattr(response, "extensions", None) or {}).get("network_stream")
    peer = None
    if stream is not None and hasattr(stream, "get_extra_info"):
        try:
            peer = stream.get_extra_info("server_addr")
        except (AttributeError, OSError, TypeError):
            peer = None
    # Csak a valdi, hossz-IPv4/6 alak fogadható el: egy MagicMock peer
    # hamis elutasitast okozna, ezert a truthy es nem-str tipus kiszurove.
    if isinstance(peer, (tuple, list)) and peer:
        host = str(peer[0])
    elif isinstance(peer, str) and peer:
        host = peer
    else:
        host = ""
    if host:
        _verify_peer_ip(host)
        return
    host = getattr(getattr(request, "url", None), "host", None)
    if host:
        for address in _resolve_addresses(str(host)):
            _verify_peer_ip(address)




def _resolve_addresses(host: str) -> list[str]:
    # A feloldas hataridot kap: egy blackhole DNS a teljes keres idejet
    # kitehetne, es a szal lezarasa nem varna ra (SSRF-7).
    raw_infos = _resolve_with_deadline(host)
    seen: set[str] = set()
    addresses: list[str] = []
    for info in raw_infos:
        _, _, _, _, sockaddr = info
        addr = sockaddr[0]
        if addr not in seen:
            seen.add(addr)
            addresses.append(addr)
    if not addresses:
        raise ValueError(f"unresolvable host: {host}")
    return addresses


def validate_scheme(parsed: urllib.parse.ParseResult) -> None:
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"unsupported url scheme: {parsed.scheme}")


def validate_scheme_and_host(url: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url)
    validate_scheme(parsed)
    if not parsed.hostname:
        raise ValueError("url host missing")
    if _is_blocked_host(parsed.hostname):
        raise ValueError(f"blocked hostname: {parsed.hostname}")
    return parsed


def validate_resolved_ips(host: str | None) -> list[str]:
    if not host:
        raise ValueError("url host missing")
    addresses = _resolve_addresses(host)
    for addr in addresses:
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError as exc:
            raise ValueError(f"invalid resolved ip: {addr}") from exc
        if _is_reserved(ip):
            raise ValueError(f"reserved ip rejected: {ip}")
    return addresses


def validate_image_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    validate_scheme(parsed)
    if not parsed.hostname:
        raise ValueError("url host missing")
    if _is_blocked_host(parsed.hostname):
        raise ValueError(f"blocked hostname: {parsed.hostname}")
    validate_resolved_ips(parsed.hostname)


def resolve_and_validate(url: str, max_bytes: int = _DEFAULT_MAX_BYTES) -> urllib.parse.ParseResult:
    parsed = validate_scheme_and_host(url)
    validate_resolved_ips(parsed.hostname)
    return parsed


def validate_url(url: str, max_bytes: int = _DEFAULT_MAX_BYTES) -> httpx.Request:
    parsed = validate_scheme_and_host(url)
    return httpx.Request(method="GET", url=urllib.parse.urlunparse(parsed))


def validate_response_headers(headers) -> None:
    if headers is None:
        return
    content_length = headers.get("Content-Length") or headers.get("content-length")
    if content_length is None:
        return
    try:
        int(content_length)
    except (TypeError, ValueError):
        raise ValueError("invalid content-length")


def count_bytes(iterable: IterableType[bytes], max_bytes: int) -> Iterator[bytes]:
    total = 0
    for chunk in iterable:
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"response exceeds max bytes: {total}")
        yield chunk


def _normalize_redirect_url(base_url: str, location: str) -> urllib.parse.ParseResult:
    if location.startswith(("http://", "https://")):
        return urllib.parse.urlparse(location)
    return urllib.parse.urlparse(urllib.parse.urljoin(base_url, location))


def _build_validated_request(parsed: urllib.parse.ParseResult) -> httpx.Request:
    if not parsed.hostname:
        raise ValueError("url host missing")
    if _is_blocked_host(parsed.hostname):
        raise ValueError(f"blocked redirect host: {parsed.hostname}")
    # SSRF safety: validate the resolved IPs (rejects reserved/private ranges)
    # but KEEP the hostname in the request URL. Replacing the host with its IP
    # breaks TLS SNI/cert verification for hosts that resolve to IPv6 first
    # (BUG-002: "certificate verify failed: IP address mismatch").
    validate_resolved_ips(parsed.hostname)
    netloc = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
    target = parsed._replace(netloc=netloc)
    return httpx.Request(method="GET", url=urllib.parse.urlunparse(target))


class _SSRFGuardClient:
    def __init__(self, max_redirects: int = 5) -> None:
        self._max_redirects = max_redirects
        self._redirect_depth = 0

    def fetch(self, request: httpx.Request, max_bytes: int = _DEFAULT_MAX_BYTES) -> bytes:
        timeout = httpx.Timeout(connect=10.0, read=30.0, write=None, pool=None)
        with httpx.Client(timeout=timeout) as client:
            return self._send(client, request, max_bytes=max_bytes, buffer=bytearray())

    def _send(
        self,
        client: httpx.Client,
        request: httpx.Request,
        *,
        max_bytes: int,
        buffer: bytearray,
        deadline: float | None = None,
    ) -> bytes:
        # A teljes keresre vonatkozo idokeret: 5 redirect x 30s egyebkent
        # korlatlan ideig futhatna (DoS-kepesség).
        if _deadline_expired(deadline):
            raise ValueError("total fetch timeout exceeded")
        if self._redirect_depth >= self._max_redirects:
            raise ValueError("too many redirects")
        base_parsed = urllib.parse.urlparse(str(request.url))
        base_parsed = base_parsed._replace(netloc=base_parsed.hostname)
        validated = _build_validated_request(base_parsed)
        response = client.send(validated, stream=True)
        try:
            # SSRF-1: a DNS-lookup ellenorzes NEM eleg — a kapcsolat
            # tenyleges peer IP-jét is ellenorizzuk (DNS-rebinding / TOCTOU).
            _verify_actual_peer(validated, response)
            if response.is_redirect:
                # Do not consume redirect body — just follow Location.
                location = response.headers.get("Location")
                if not location:
                    raise ValueError("redirect missing location")
                self._redirect_depth += 1
                next_parsed = _normalize_redirect_url(str(request.url), location)
                # Validate redirect target: scheme, hostname blocklist, and resolved IPs
                if not next_parsed.hostname:
                    raise ValueError("redirect target missing host")
                if _is_blocked_host(next_parsed.hostname):
                    raise ValueError(f"blocked redirect host: {next_parsed.hostname}")
                validate_resolved_ips(next_parsed.hostname)
                next_request = _build_validated_request(next_parsed)
                response.close()
                return self._send(
                    client,
                    next_request,
                    max_bytes=max_bytes,
                    buffer=bytearray(),
                    deadline=deadline,
                )

            # A max_bytes a DEKODOLATLAN meretet korlatozza, igy a tomorites
            # megkerulhato -> a valasz kodolasat itt ellenorizzuk.
            _reject_compressed_response(validated, response)

            # Non-redirect: validate content type before streaming.
            content_type = response.headers.get("Content-Type")
            if not (isinstance(content_type, str) and content_type.startswith("image/")):
                raise ValueError("non-image content type")

            content_length = response.headers.get("Content-Length")
            allowed = max_bytes if content_length is None else min(int(content_length), max_bytes)
            for chunk in count_bytes(response.iter_raw(chunk_size=65536), allowed):
                buffer.extend(chunk)
            return bytes(buffer)
        finally:
            response.close()


def fetch_image_bytes(
    url: str,
    *,
    max_bytes: int = _DEFAULT_MAX_BYTES,
    timeout: float = _DEFAULT_TIMEOUT,
) -> bytes:
    try:
        request = validate_url(url, max_bytes=max_bytes)
        guard = _SSRFGuardClient()
        client_timeout = httpx.Timeout(connect=10.0, read=timeout, write=None, pool=None)
        with httpx.Client(timeout=client_timeout) as http_client:
            return guard._send(
                http_client,
                request,
                max_bytes=max_bytes,
                buffer=bytearray(),
                deadline=time.monotonic() + _DEFAULT_TOTAL_TIMEOUT,
            )
    except httpx.InvalidURL as exc:
        logger.warning("Invalid URL rejected: %s", exc)
        raise HTTPException(
            status_code=400, detail="Invalid image URL."
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("HTTP error fetching image: %s", exc)
        raise HTTPException(
            status_code=400, detail="Failed to fetch image from URL."
        ) from exc
    except socket.gaierror as exc:
        logger.warning("DNS resolution failed: %s", exc)
        raise HTTPException(
            status_code=400, detail="Failed to fetch image from URL."
        ) from exc
    except ValueError as exc:
        message = str(exc)
        if message == "non-image content type":
            raise HTTPException(status_code=400, detail="URL did not return an image") from exc
        if message.startswith("response exceeds max bytes"):
            raise HTTPException(status_code=400, detail="Image exceeds maximum allowed size") from exc
        logger.warning("Validation error fetching image: %s", exc)
        raise HTTPException(
            status_code=400, detail="Failed to fetch image from URL."
        ) from exc
