"""SSRF cim-ellenorzesi primitivek (DNS-fuggetlen resz)."""
from __future__ import annotations
import ipaddress
import socket
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
_BLOCKED_HOSTNAME_SUBSTRINGS = ("local", "internal", "localhost")
_BLOCKED_HOSTNAME_EXACT = frozenset({"localhost", "local.host", "metadata.google.internal", "metadata.internal", "169.254.169.254", "metadata"})
_RESERVED_NETWORKS = [ipaddress.ip_network("127.0.0.0/8"), ipaddress.ip_network("::1/128"), ipaddress.ip_network("10.0.0.0/8"), ipaddress.ip_network("172.16.0.0/12"), ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("169.254.0.0/16"), ipaddress.ip_network("fe80::/10"), ipaddress.ip_network("100.64.0.0/10"), ipaddress.ip_network("224.0.0.0/4"), ipaddress.ip_network("240.0.0.0/4"), ipaddress.ip_network("0.0.0.0/8"), ipaddress.ip_network("::/128"), ipaddress.ip_network("fc00::/7"), ipaddress.ip_network("192.0.0.0/24"), ipaddress.ip_network("192.0.2.0/24"), ipaddress.ip_network("198.51.100.0/24"), ipaddress.ip_network("203.0.113.0/24"), ipaddress.ip_network("255.255.255.255/32"), ipaddress.ip_network("2001:db8::/32"), ipaddress.ip_network("100::/64")]
_DEFAULT_TOTAL_TIMEOUT = 45.0
def _is_reserved(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Beagyazott IPv4 kinyerese IPv6 kulonleges tartomanyokbol
    if address.version == 6:
        # IPv4-mapped cim (::ffff:a.b.c.d)
        if address.ipv4_mapped is not None:
            # Rekurziv vizsgalat IPv4-kent (pl. ::ffff:127.0.0.1)
            if _is_reserved(address.ipv4_mapped):
                return True
        # NAT64 prefix, az utolso 32 bit a beagyazott IPv4
        elif address.packed[:12] == b"\x00\x64\xff\x9b\x00\x00\x00\x00\x00\x00\x00\x00":
            if _is_reserved(ipaddress.IPv4Address(address.packed[12:])):
                return True
        # 6to4 prefix, a 3-6. bajt a beagyazott IPv4
        elif address.packed[:2] == b"\x20\x02":
            if _is_reserved(ipaddress.IPv4Address(address.packed[2:6])):
                return True
    # Beepitett flag-ek, a fenti dekodolas utan (mapped eseten nem megbizhatok)
    if address.is_loopback or address.is_private or address.is_reserved or address.is_multicast or address.is_unspecified:
        return True
    # Kezi tiltolista (CGNAT es 240/4 nincs a flag-ekben)
    return any(address in network for network in _RESERVED_NETWORKS)
def _deadline_expired(deadline: float | None) -> bool:
    """True ha a monotonic hataridok lejart (monoton, nem wall-clock)."""
    if deadline is None:
        return False
    return time.monotonic() > deadline
def _verify_peer_ip(address: str) -> None:
    """Ellenőrli a kapcsolat ténylegesen kapott IP-jét; ValueError ha privát.
    A TOCTOU (DNS-rebinding) ellenszora: nem elég a DNS-lookupot ellenőrizni,
    a tényleges peer IP-t is. Ascendens a _is_reserved felett.
    """
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValueError(f"unparseable peer ip: {address}") from exc
    if _is_reserved(parsed):
        raise ValueError(f"reserved peer ip rejected: {address}")
def _resolve_with_deadline(host: str, timeout: float = 5.0) -> list:
    """socket.getaddrinfo határidővel; ValueError ha a DNS nem válaszol.
    A fekete lyuk (blackhole) DNS ellen: külön szálban kérdezünk, és a
    pool lezárása NEM vár rá — a hívó a határidőn pontosan szabadul fel.
    """
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(socket.getaddrinfo, host, None)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeoutError as exc:
        raise ValueError(f"dns timeout: {host}") from exc
    finally:
        # wait=False: a legradulo DNS-szal ne tartsa benne a hívot.
        pool.shutdown(wait=False)
def _reject_compressed_response(request: object, response: object) -> None:
    """Letiltja a tömörített választ; ValueError ha a szerver Content-Encoding-et küld.
    A max_bytes a DEKÓDOLATLAN (tömörített) méretet korlátozza, így egy kis
    gzip-arf 1 GB-ra hízhat — a kicsomagolt méret korlátlan maradna.
    """
    headers = getattr(request, "headers", None)
    if headers is not None:
        try:
            headers["Accept-Encoding"] = "identity"
        except (AttributeError, TypeError, KeyError):
            pass  # a header nem módosítható -> a Content-Encoding ellenőrzés dönt
    raw = (getattr(response, "headers", None) or {}).get("Content-Encoding")
    # Csak a valodi string header erdekes: a teszt-mock-ok (MagicMock) a
    # hianylo fejlecet egy mock objektumkent adnak vissza, ami szintén
    # "nem identity" lenne -> hamis elutasitas.
    encoding = str(raw).strip().lower() if isinstance(raw, str) else "identity"
    if encoding not in ("", "identity"):
        raise ValueError("content encoding not allowed")
def _is_blocked_host(host: str) -> bool:
    """Belső/metadata hostnevek és numerikus IP-kijátszások blokkolása."""
    host = unicodedata.normalize("NFKC", host)
    host = host.strip().strip(".").lower()
    if host in _BLOCKED_HOSTNAME_EXACT:
        return True
    for suffix in _BLOCKED_HOSTNAME_SUBSTRINGS:
        if host == suffix or host.endswith("." + suffix):
            return True
    try:
        # A szokásos IPv4/IPv6 literalt ne itt dekduljuk fel: az a
        # validate_resolved_ips foglalja (a "reserved ip rejected" uzenet
        # onnan jon, es a hivasok arra epulnek). Itt csak a NEM-szabalyos
        # numerikus alakokat (hex, octalis, decimal) nezzuk meg.
        if "." not in host and ":" not in host:
            try:
                val = int(host, 0)
            except ValueError:
                if host.isdigit() and len(host) > 1 and host[0] == "0":
                    val = int(host, 8)
                else:
                    raise
            if 0 <= val <= 4294967295:
                ip = ipaddress.IPv4Address(val)
                # A szam-jellegu alakot a _is_reserved donti el (a nevlista
                # a hostnevekre vonatkozik, nem a feloldott cimekre).
                if _is_reserved(ip):
                    return True
        elif "." in host and ":" not in host:
            parts = host.split(".")
            # A szabalyos decimalis IPv4 literalt hagyjuk a
            # validate_resolved_ips-nek: a 0-elejU (octalis) vagy nem-10
            # radixu (hex) reszek itt a "nem szabalyos" alak jelei.
            non_decimal = any(p.startswith("0") and len(p) > 1 or p.lower().startswith("0x") for p in parts)
            if len(parts) == 4 and all(parts) and non_decimal:
                nums = []
                for p in parts:
                    try:
                        n = int(p, 0)
                    except ValueError:
                        if p.isdigit() and len(p) > 1 and p[0] == "0":
                            n = int(p, 8)
                        else:
                            raise
                    nums.append(n)
                if all(0 <= n <= 255 for n in nums):
                    ip = ipaddress.IPv4Address(".".join(str(n) for n in nums))
                    if _is_reserved(ip):
                        return True
    except ValueError:
        pass
    return False
__all__ = ["_is_reserved", "_deadline_expired", "_verify_peer_ip", "_resolve_with_deadline", "_reject_compressed_response", "_is_blocked_host"]
