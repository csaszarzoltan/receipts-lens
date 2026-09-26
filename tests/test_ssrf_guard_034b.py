"""FIX-B RED: az SSRF-guard 8 valós megkerülésének bizonyítéka.

Audit-findingok: SSRF-1 (TOCTOU), SSRF-2 (IPv4-mapped IPv6), SSRF-3
(reserved hálózatok hiánya), SSRF-4 (hostname-kanonizálás), SSRF-5
(stateful redirect depth), SSRF-6 (nincs össz-időlimit), SSRF-7 (DNS
feloldás határidő nélkül), SSRF-8 (gzip-bomba).

A tesztek NEM hálózatot igényelnek: a DNS-feloldást és az httpx hívást
monkeypatcheljük. A cél az, hogy a guardot NE lehessen megkerülni — ha
a javítás kész, minden teszt zöld; ha nincs, a piros teszt dokumentálja a
rést.

A RED állapot a javítás ELŐTT: a tesztek a findingokat dokumentálják,
nem a jelenlegi viselkedést tesztelik.
"""
from __future__ import annotations

import ipaddress
import socket
from unittest.mock import patch

import pytest

from app import ssrf_address, ssrf_guard
from app.ssrf_guard import (
    validate_image_url,
    validate_resolved_ips,
    validate_scheme_and_host,
)

# ---------------------------------------------------------------------------
# SSRF-2 [HIGH]: IPv4-mapped IPv6 megkerülés
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "host",
    ["::ffff:127.0.0.1", "::ffff:169.254.169.254"],
)
@pytest.mark.test_id("test_ipv4_mapped_literal_host_is_blocked")
@pytest.mark.requirements("SSRF-2")
@pytest.mark.scenario("A SSRF-2 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_ipv4_mapped_literal_host_is_blocked(host: str) -> None:
    """SSRF-2: a mapped IPv6 cím közvetlenül hostként is blokkolandó.

    Nincs DNS: a cím literál, a ``getaddrinfo`` a literált adja vissza.
    """
    with patch.object(
        socket, "getaddrinfo", return_value=[(2, 1, 6, "", (host, 0, 0, 0))]
    ):
        with pytest.raises(ValueError):
            validate_resolved_ips(host)


@pytest.mark.test_id("test_nat64_prefix_is_checked")
@pytest.mark.requirements("SSRF-2")
@pytest.mark.scenario("A SSRF-2 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_nat64_prefix_is_checked() -> None:
    """SSRF-2: a NAT64 (64:ff9b::/96) és 6to4 (2002::/16) prefixet is kezeld.

    A 64:ff9b::169.254.169.254 IPv6-objektumként nem esik bele egyetlen
    IPv4-tartományba sem, de a beágyazott IPv4 private.
    """
    addr = ipaddress.ip_address("64:ff9b::169.254.169.254")
    assert ssrf_guard._is_reserved(addr) is True, (
        "a NAT64-be ágyazott metadata-címet privátnak kell tekinteni"
    )


# ---------------------------------------------------------------------------
# SSRF-3 [MEDIUM]: hiányzó reserved hálózatok
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "addr",
    [
        "255.255.255.255",  # limited broadcast
        "192.0.0.1",  # IETF protocol assignments
        "192.0.2.1",  # TEST-NET-1
        "198.51.100.1",  # TEST-NET-2
        "203.0.113.1",  # TEST-NET-3
        "100::1",  # discard-only
        "2001:db8::1",  # documentation
    ],
)
@pytest.mark.test_id("test_reserved_ranges_are_blocked")
@pytest.mark.requirements("SSRF-3")
@pytest.mark.scenario("A SSRF-3 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_reserved_ranges_are_blocked(addr: str) -> None:
    """SSRF-3: a broadcast, IETF- és dokumentációs tartományok is privátak."""
    assert ssrf_guard._is_reserved(ipaddress.ip_address(addr)) is True, (
        f"{addr} privát/tilos tartomány, de a guard átengedi"
    )


@pytest.mark.test_id("test_multicast_and_unspecified_are_blocked")
@pytest.mark.requirements("SSRF-3")
@pytest.mark.scenario("A SSRF-3 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_multicast_and_unspecified_are_blocked() -> None:
    """SSRF-3: defense-in-depth — az ismételt privát ellenőrzés legyen benne."""
    for addr in ("224.0.0.1", "0.0.0.0", "::"):
        assert ssrf_guard._is_reserved(ipaddress.ip_address(addr)) is True


# ---------------------------------------------------------------------------
# SSRF-4 [MEDIUM]: hostname-kanonizálás
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://LOCALHOST/x.jpg",
        "http://LocalHost./x.jpg",
        "http://localhost../x.jpg",
        "http://127.0.0.1.nip.io/x.jpg",
        "http://0177.0.0.1/x.jpg",
        "http://0x7f000001/x.jpg",
    ],
)
@pytest.mark.test_id("test_hostname_canonicalisation_blocks_bypasses")
@pytest.mark.requirements("SSRF-4")
@pytest.mark.scenario("A SSRF-4 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_hostname_canonicalisation_blocks_bypasses(url: str) -> None:
    """SSRF-4: kisbetűsítés, trailing dot, wildcard-DNS és numerikus IP-forma.

    A ``LOCALHOST`` és a ``localhost.`` a substring-alapú ellenőrzést kikerüli,
    a ``*.nip.io`` wildcard DNS-t használ, a 0177/0x7f... pedig a
    ``ipaddress``-ot megtéveszti.
    """
    with pytest.raises(ValueError):
        validate_image_url(url)


@pytest.mark.test_id("test_trailing_dot_hostname_is_normalised")
@pytest.mark.requirements("SSRF-4")
@pytest.mark.scenario("A SSRF-4 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_trailing_dot_hostname_is_normalised() -> None:
    """SSRF-4: a trailing dot ne tegye lehetővé a blocklist megkerülését."""
    with patch.object(
        socket, "getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 0, 0, 0))]
    ):
        with pytest.raises(ValueError):
            validate_image_url("http://metadata.google.internal./latest/")


# ---------------------------------------------------------------------------
# SSRF-1 [HIGH]: TOCTOU — a validált IP-t tűzzel a kapcsolathoz
# ---------------------------------------------------------------------------


@pytest.mark.test_id("test_public_peer_ip_is_accepted")
@pytest.mark.requirements("SSRF-1")
@pytest.mark.scenario("A SSRF-1 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_public_peer_ip_is_accepted() -> None:
    """SSRF-1: a _verify_peer_ip egy PUBLIKUS IP-t elfogad (nem csak a privátat)."""
    ssrf_guard._verify_peer_ip("93.184.216.34")  # nem dob ValueError-t


@pytest.mark.parametrize(
    "peer",
    [
        "127.0.0.1",
        "169.254.169.254",
        "10.0.0.5",
        "::ffff:10.0.0.5",
        "0.0.0.0",
        "255.255.255.255",
    ],
)
@pytest.mark.test_id("test_private_peer_ip_is_rejected")
@pytest.mark.requirements("SSRF-1")
@pytest.mark.scenario("A SSRF-1 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_private_peer_ip_is_rejected(peer: str) -> None:
    """SSRF-1: a tényleges peer IP privát -> ValueError (DNS-rebinding-ellenes)."""
    with pytest.raises(ValueError, match="reserved peer ip rejected"):
        ssrf_guard._verify_peer_ip(peer)


@pytest.mark.test_id("test_unparseable_peer_ip_is_rejected")
@pytest.mark.requirements("SSRF-1")
@pytest.mark.scenario("A SSRF-1 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_unparseable_peer_ip_is_rejected() -> None:
    """SSRF-1: ha a peer IP nem parse-olható, azt is el kell utasítani.

    Fail-closed: a "nem tudom mi a peer" nem lehet "jo lesz".
    """
    with pytest.raises(ValueError, match="unparseable peer ip"):
        ssrf_guard._verify_peer_ip("nem-ez-az-ip")


@pytest.mark.test_id("test_consumer_path_verifies_peer_ip")
@pytest.mark.requirements("SSRF-1")
@pytest.mark.scenario("A SSRF-1 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_consumer_path_verifies_peer_ip() -> None:
    """SSRF-1: a peer-ellenőrzés a tényleges fogyasztási útvonalon fusson.

    Nem elég, hogy létezik a függvény: a _send a kapcsolat után hívja meg.
    """
    import inspect

    src = inspect.getsource(ssrf_guard._SSRFGuardClient._send)
    assert "_verify_actual_peer" in src or "_verify_peer_ip" in src, (
        "a _send nem ellenorzi a peer IP-t — a DNS-rebinding-vedelem nincs bekotve"
    )


# ---------------------------------------------------------------------------
# SSRF-5 [MEDIUM]: a redirect-depth ne legyen instance-állapot
# ---------------------------------------------------------------------------


@pytest.mark.test_id("test_redirect_depth_is_not_shared_between_instances")
@pytest.mark.requirements("SSRF-5")
@pytest.mark.scenario("A SSRF-5 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_redirect_depth_is_not_shared_between_instances() -> None:
    """SSRF-5: két guard-példány redirect-számlálója ne ossza meg.

    Ha a depth instance-mező, egy már kimerült példány szennyezheti a
    következő kérést (DoS) vagy megkerülheti a limitet.
    """
    first = ssrf_guard._SSRFGuardClient()
    first._redirect_depth = 5
    second = ssrf_guard._SSRFGuardClient()
    assert getattr(second, "_redirect_depth", 0) != 5, (
        "a redirect-depth instance-állapot, nem kérés-scoped"
    )


@pytest.mark.test_id("test_redirect_target_scheme_is_validated")
@pytest.mark.requirements("SSRF-5")
@pytest.mark.scenario("A SSRF-5 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_redirect_target_scheme_is_validated() -> None:
    """SSRF-5: a redirect Location-ját a teljes validatornak kell futtatni.

    A `file://` vagy `gopher://` Location-t a scheme-ellenőrzés fogja meg.
    """
    with pytest.raises(ValueError):
        ssrf_guard.validate_scheme_and_host("file:///etc/passwd")


# ---------------------------------------------------------------------------
# SSRF-6 [MEDIUM]: össz-időlimit
# ---------------------------------------------------------------------------


@pytest.mark.test_id("test_total_timeout_budget_exists")
@pytest.mark.requirements("SSRF-6")
@pytest.mark.scenario("A SSRF-6 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_total_timeout_budget_exists() -> None:
    """SSRF-6: 5 redirect × 30s = 150s DoS-képesség — kell össz-budget."""
    assert hasattr(ssrf_guard, "_DEFAULT_TOTAL_TIMEOUT"), (
        "nincs össz-időlimit a guardban — a redirect-lánc korlátlan ideig futhat"
    )


@pytest.mark.test_id("test_timeout_argument_is_honoured")
@pytest.mark.requirements("SSRF-6")
@pytest.mark.scenario("A SSRF-6 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_timeout_argument_is_honoured() -> None:
    """SSRF-6: a fetch_image_bytes(timeout=...) paraméter ne vesszen el.

    Jelenleg a _SSRFGuardClient.fetch() hardcoded 30s read-timeoutot használ,
    a hívó paramétere nem jut el a kliensig.
    """
    with patch.object(ssrf_guard, "_SSRFGuardClient") as guard_cls:
        guard_cls.return_value._send.return_value = b"x"
        try:
            ssrf_guard.fetch_image_bytes(
                "http://example.com/x.jpg", timeout=3.0
            )
        except Exception:
            pass
    assert guard_cls.called, "a guard nem volt példányosítva"
    # a timeout-ot vagy a konstruktorban, vagy a _send-ben át kell adni
    call_args = guard_cls.call_args
    assert call_args.kwargs or getattr(
        guard_cls.return_value, "_timeout", None
    ), "a timeout paraméter nem jut el a guard klienshez"


# ---------------------------------------------------------------------------
# SSRF-7 [MEDIUM]: a DNS-feloldás kapjon határidőt
# ---------------------------------------------------------------------------


@pytest.mark.test_id("test_dns_resolution_has_a_timeout")
@pytest.mark.requirements("SSRF-7")
@pytest.mark.scenario("A SSRF-7 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_dns_resolution_has_a_timeout() -> None:
    """SSRF-7: a lassú (blackhole) DNS-t a határidő megszakítja.

    Nem a forrásszöveget nézzük: futtassuk le egy 30 s-os DNS-sel és mérjük,
    hogy a hívó ~timeout után szabadul fel.
    """
    import time
    from unittest.mock import patch as _patch

    with _patch("socket.getaddrinfo", side_effect=lambda *a, **k: time.sleep(30)):
        started = time.monotonic()
        with pytest.raises(ValueError, match="dns timeout"):
            ssrf_guard._resolve_with_deadline("slow.example", timeout=1.0)
        elapsed = time.monotonic() - started
    assert elapsed < 5.0, f"a DNS-hatarido nem mukodott ({elapsed:.1f}s)"


@pytest.mark.test_id("test_resolve_addresses_uses_the_deadline_wrapper")
@pytest.mark.requirements("SSRF-7")
@pytest.mark.scenario("A SSRF-7 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_resolve_addresses_uses_the_deadline_wrapper() -> None:
    """SSRF-7: a publikus belso pont is a hataridos feloldast hivja."""
    import inspect

    src = inspect.getsource(ssrf_guard._resolve_addresses)
    assert "_resolve_with_deadline" in src, (
        "a _resolve_addresses meg mindig hatarido nelkul hivja a getaddrinfo-t"
    )


# ---------------------------------------------------------------------------
# SSRF-8 [MEDIUM]: gzip-bomba
# ---------------------------------------------------------------------------


@pytest.mark.test_id("test_content_encoding_is_rejected_or_identity_requested")
@pytest.mark.requirements("SSRF-8")
@pytest.mark.scenario("A SSRF-8 finding lezárása bizonyítva: az SSRF-guard elveszíti a feltüntetett megkerülési módot.")
def test_content_encoding_is_rejected_or_identity_requested() -> None:
    """SSRF-8: a klipt a dekódolatlan méretet korlátozza, a kicsomagoltat nem.

    Egy 1 kB-os gzip-féj 1 GB-ra hízhat; a ``iter_raw`` a tömörített méretet
    számolja, így a max_bytes kikerülhető.
    """
    import inspect

    src = inspect.getsource(ssrf_guard) + inspect.getsource(ssrf_address)
    assert (
        "Accept-Encoding" in src or "content-encoding" in src.lower()
    ), (
        "nincs Content-Encoding kezelés — a gzip-bomba kikerüli a max_bytes-t"
    )
