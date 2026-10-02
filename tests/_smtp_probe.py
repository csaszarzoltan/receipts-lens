"""F2.5 price-alert probe: a real SMTP conversation against a local mock.

The F2.5 acceptance claim is that a price hike travels the whole path --
SMTP ``DATA`` is accepted (250 + queue-id) *and* a ``price_alert_sent`` row
is written -- without a real email ever leaving the machine.  That claim
cannot be proven by a patched ``smtplib``: the interesting behaviour lives
in the wire protocol the client actually speaks.

So this module stands up a minimal SMTP responder on 127.0.0.1 (ephemeral
port) and points the CLI at it by overriding the five SMTP keys in the
child environment.  Everything else comes from the repo's real ``.env``.

``RECEIPTLENS_PRODUCT_DB`` is overridden too, but with a *throwaway copy*
of the real database: the key resolves both the tenant's subscriptions and
the alert recipient, so the probe needs real rows -- but the run writes a
``price_alert_sent`` ledger row, and that row must never land in the live
database.  :func:`_isolated_db` copies the live file with SQLite's backup
API (consistent even under concurrent writers, unlike a file copy), clears
the ledger, and the run reads its result back from that copy.  A guard in
:func:`run_cli_against_mock` refuses to run if the path ever resolves back
to the live file.

Implementation notes that are load-bearing, not incidental:

* **Raw socket, not ``smtpd``.**  ``smtpd`` emits a ``DeprecationWarning``
  and is removed in Python 3.12; the protocol surface needed here is small
  enough to implement directly, and a raw socket keeps full control over
  exactly which extensions are advertised.
* **STARTTLS is deliberately NOT advertised.**  ``send_email_notification``
  calls ``smtp.starttls()`` whenever ``has_extn("starttls")`` is true
  (app/subscription_alerts.py:524).  This mock is plaintext-only, so the
  EHLO reply must omit the extension or the client would begin a TLS
  handshake against a server that cannot complete one.
* **The CLI is invoked through ``app.cli:main``, not ``python -m app.cli``.**
  ``app/cli.py`` has no ``__main__`` guard, so ``python -m app.cli`` exits 0
  having run nothing at all -- a silent no-op that would make this probe
  report success while no mail was ever attempted.

Credential handling: this module reads ``.env`` (acceptable for a test
helper) but never prints or logs a credential value.  Member addresses are
PII; the owner is addressed through the SMTP dialogue rather than printed.
"""

from __future__ import annotations

import os
import pathlib
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = REPO_ROOT / ".env"

# The mock accepts any AUTH credentials -- it never validates them -- but the
# client only attempts LOGIN when both a user and a password are present.
_MOCK_USER = "probe-user"
_MOCK_PASSWORD = "probe-password"
_MOCK_FROM = "receiptlens-probe@example.com"


class Capture:
    """Collects what the mock server received.

    ``messages`` holds one dict per completed DATA payload, each with keys
    ``mail_from``, ``rcpt_to`` (a list) and ``data`` (the raw bytes, not
    decoded -- decoding is the caller's choice of encoding).
    """

    def __init__(self) -> None:
        self.messages: list[dict] = []
        self._lock = threading.Lock()

    def add(self, message: dict) -> None:
        """Record one delivered message."""
        with self._lock:
            self.messages.append(message)

    def last(self) -> dict | None:
        """The most recently captured message, or ``None`` if there was none."""
        with self._lock:
            return self.messages[-1] if self.messages else None


class _MockSMTP:
    """A single-connection plaintext SMTP responder.

    Handles exactly what the client sends: EHLO, AUTH LOGIN/PLAIN,
    MAIL FROM, RCPT TO, DATA, QUIT.  Anything else gets a 500, which is
    enough for ``smtplib`` to surface an error rather than hang.
    """

    _HOSTNAME = "receiptlens-smtp-probe.invalid"

    def __init__(self, capture: Capture) -> None:
        self.capture = capture

    # -- wire helpers ---------------------------------------------------

    @staticmethod
    def _extract_address(argument: str) -> str:
        """Pull the address out of ``FROM:<a@b> PARAM=x`` style arguments."""
        match = re.search(r"<([^>]*)>", argument)
        if match:
            return match.group(1)
        return argument.split(":", 1)[-1].strip()

    def _serve(self, conn: socket.socket) -> None:
        stream = conn.makefile("rwb")
        queue_id = 0

        def reply(text: str) -> None:
            stream.write(text.encode("ascii") + b"\r\n")
            stream.flush()

        reply("220 " + self._HOSTNAME + " ESMTP receiptlens-probe")

        mail_from: str | None = None
        rcpt_to: list[str] = []
        try:
            while True:
                raw = stream.readline()
                if not raw:
                    break
                line = raw.decode("utf-8", "replace").rstrip("\r\n")
                upper = line.upper()

                if upper.startswith("EHLO"):
                    # Two lines: the hostname, then the extension list.  No
                    # STARTTLS and no SMTPUTF8 -- see the module docstring.
                    reply("250-" + self._HOSTNAME)
                    reply("250 AUTH LOGIN PLAIN")
                elif upper.startswith("HELO"):
                    reply("250 " + self._HOSTNAME)
                elif upper.startswith("AUTH LOGIN"):
                    parts = line.split()
                    if len(parts) < 3:
                        reply("334 " + _b64(b"Username:"))
                        stream.readline()  # base64 username
                        reply("334 " + _b64(b"Password:"))
                        stream.readline()  # base64 password
                    reply("235 2.7.0 Authentication successful")
                elif upper.startswith("AUTH PLAIN"):
                    parts = line.split()
                    if len(parts) < 3:
                        reply("334 ")
                        stream.readline()  # base64 blob
                    reply("235 2.7.0 Authentication successful")
                elif upper.startswith("MAIL FROM"):
                    mail_from = self._extract_address(line)
                    rcpt_to = []
                    reply("250 2.1.0 Sender ok")
                elif upper.startswith("RCPT TO"):
                    rcpt_to.append(self._extract_address(line))
                    reply("250 2.1.5 Recipient ok")
                elif upper.startswith("DATA"):
                    if mail_from is None or not rcpt_to:
                        # RFC 5321: DATA needs a valid transaction first.
                        reply("503 5.5.1 Bad sequence of commands")
                        continue
                    reply("354 End data with <CR><LF>.<CR><LF>")
                    payload = _read_data_payload(stream)
                    queue_id += 1
                    self.capture.add(
                        {
                            "mail_from": mail_from,
                            "rcpt_to": list(rcpt_to),
                            "data": payload,
                        }
                    )
                    reply(f"250 2.0.0 Ok: queued as PROBE{queue_id:08X}")
                elif upper.startswith("RSET"):
                    mail_from, rcpt_to = None, []
                    reply("250 2.0.0 Ok")
                elif upper.startswith("NOOP"):
                    reply("250 2.0.0 Ok")
                elif upper.startswith("QUIT"):
                    reply("221 2.0.0 Bye")
                    break
                else:
                    reply("500 5.5.2 Command not recognized")
        except (OSError, ValueError):
            # A client that hung up mid-dialog is normal here; nothing to do.
            pass
        finally:
            try:
                stream.close()
            except OSError:
                pass


def _b64(raw: bytes) -> str:
    """Base64-encode a credential challenge without importing for one call."""
    import base64

    return base64.b64encode(raw).decode("ascii")


def _read_data_payload(stream) -> bytes:
    """Read a DATA payload up to the terminating ``\\r\\n.\\r\\n``.

    Returns the de-terminated message bytes.  Dot-stuffing (a leading ``.``
    doubled) is undone, per RFC 5321 section 4.5.2.
    """
    lines: list[bytes] = []
    while True:
        raw = stream.readline()
        if not raw:
            break
        if raw in (b".\r\n", b".\n"):
            break
        if raw.startswith(b".."):
            raw = raw[1:]
        lines.append(raw)
    return b"".join(lines)


class _MockSMTPServer:
    """Binds an ephemeral loopback port and serves :class:`_MockSMTP`."""

    def __init__(self, capture: Capture) -> None:
        self.capture = capture
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(8)
        self._socket.settimeout(0.5)
        self.port: int = self._socket.getsockname()[1]
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._thread = threading.Thread(
            target=self._serve_forever, name="mock-smtp", daemon=True
        )
        self._thread.start()

    def _serve_forever(self) -> None:
        responder = _MockSMTP(self.capture)
        while not self._stop.is_set():
            try:
                conn, _ = self._socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            conn.settimeout(15)
            threading.Thread(
                target=self._handle, args=(responder, conn), daemon=True
            ).start()

    @staticmethod
    def _handle(responder: _MockSMTP, conn: socket.socket) -> None:
        try:
            responder._serve(conn)
        finally:
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.close()

    def close(self) -> None:
        """Stop accepting and release the listening socket."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
        try:
            self._socket.close()
        except OSError:
            pass


def _load_env() -> dict[str, str]:
    """Parse the repo's real ``.env`` into a dict.

    Deliberately hand-rolled rather than pulling in python-dotenv: the file is
    simple ``KEY=value`` and this helper must not add a dependency.
    """
    values: dict[str, str] = {}
    if not _ENV_FILE.is_file():
        return values
    for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _isolated_db() -> str:
    """Copy the live schema + needed rows into a temp DB; return path."""
    live = pathlib.Path(__file__).resolve().parent.parent / "receiptlens-product.db"
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="smtp-probe-"))
    dest = tmpdir / "probe.db"
    src = sqlite3.connect(live)
    out = sqlite3.connect(dest)
    src.backup(out)
    src.close()
    out.execute("DELETE FROM price_alert_sent")
    out.commit()
    out.close()
    return str(dest)


def _child_env(port: int, db_path: str) -> dict[str, str]:
    """The child environment: real ``.env``, with the SMTP keys overridden.

    Only the five SMTP keys are replaced, plus ``RECEIPTLENS_PRODUCT_DB``,
    which points at the throwaway copy from :func:`_isolated_db`.  The copy
    must carry the real rows, because that key is what resolves the tenant's
    subscriptions and the active owner -- without them the service falls back
    to an empty database and the run would suppress the alert instead of
    sending it.  The *path* must not be the live one, or the ledger row this
    run writes would be a write to production data.
    """
    env = _load_env()
    env["RECEIPTLENS_SMTP_HOST"] = "127.0.0.1"
    env["RECEIPTLENS_SMTP_PORT"] = str(port)
    env["RECEIPTLENS_SMTP_USER"] = _MOCK_USER
    env["RECEIPTLENS_SMTP_PASSWORD"] = _MOCK_PASSWORD
    env["RECEIPTLENS_SMTP_FROM"] = _MOCK_FROM
    # The send path refuses to dial out unless this opt-in is present.
    env["RECEIPTLENS_SMTP_ENABLED"] = "1"
    # An inherited address like a stale POSTMASTER would break our 500 default.
    env.pop("RECEIPTLENS_SMTP_FROM_ADDR", None)
    env["RECEIPTLENS_PRODUCT_DB"] = db_path
    return env


def _count_ledger_rows(tenant: str, db_path: str) -> int:
    """Count ``price_alert_sent`` rows for ``tenant``, read after the run.

    Reads ``db_path`` -- the same throwaway copy the child wrote to -- not the
    database named in ``.env``, so a passing probe says nothing at all about
    the live ledger.
    """
    resolved = db_path if os.path.isabs(db_path) else str(REPO_ROOT / db_path)
    if not Path(resolved).is_file():
        return 0
    conn = sqlite3.connect(resolved)
    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM price_alert_sent WHERE tenant_id = ?", (tenant,)
        )
        return int(cursor.fetchone()[0])
    finally:
        conn.close()


def _read_ledger_row(tenant: str, db_path: str) -> dict | None:
    """Return the single ``price_alert_sent`` row for ``tenant`` as a dict.

    ``None`` unless there is exactly one row: with zero rows there is nothing
    to inspect, and with two or more there is no single row to speak of, so
    the caller must assert on the count first.  Every column is returned, so
    the caller asserts on names rather than positional indexes.

    ``db_path`` is the throwaway copy, which is why this has to run *before*
    the cleanup in :func:`run_cli_against_mock`.
    """
    count = _count_ledger_rows(tenant, db_path)
    if count != 1:
        return None
    resolved = db_path if os.path.isabs(db_path) else str(REPO_ROOT / db_path)
    conn = sqlite3.connect(resolved)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            "SELECT * FROM price_alert_sent WHERE tenant_id = ?", (tenant,)
        )
        row = cursor.fetchone()
        return dict(row) if row is not None else None
    finally:
        conn.close()


def run_cli_against_mock(tenant: str) -> dict:
    """Run the real price-alert CLI against the mock and report what happened.

    Spawns ``app.cli:main(['subscription-alerts', '--tenant', tenant])`` --
    **not** ``--dry-run``, since a dry run suppresses both the send and the
    ledger write and would prove nothing -- in a child process whose
    environment carries the real ``.env`` with only the SMTP keys pointed at
    the mock.

    Returns a dict with ``returncode``, ``stdout``, ``stderr``, ``message``
    (the last captured message, or ``None``), ``ledger_rows`` (the
    ``price_alert_sent`` count for the tenant read *after* the run),
    ``ledger_row`` (that row as a plain ``column -> value`` dict, or ``None``
    if ``ledger_rows != 1``), ``db_path`` and ``port``.

    The row is materialised **inside** this function, before the ``finally``
    below deletes the throwaway copy -- the path alone would not let a caller
    read it afterwards.  ``ledger_rows`` is read from that copy, and the live
    database is never written by this function.
    """
    capture = Capture()
    server = _MockSMTPServer(capture)
    db_value = _isolated_db()
    server.start()
    try:
        live = (pathlib.Path(__file__).resolve().parent.parent
                / "receiptlens-product.db")
        if pathlib.Path(db_value).resolve() == live.resolve():
            raise RuntimeError("probe refuses to run against the live DB")
        # `python -m app.cli` would exit 0 without running anything: app/cli.py
        # has no __main__ guard.  Drive main() explicitly and let its return
        # value become the process exit code.
        code = (
            "from app.cli import main;"
            "raise SystemExit(main(['subscription-alerts','--tenant',%r]))" % tenant
        )
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(REPO_ROOT),
            env=_child_env(server.port, db_value),
            capture_output=True,
            text=True,
            timeout=180,
        )
        # Both reads happen here, while the throwaway copy still exists: the
        # `finally` below removes it before the caller ever sees this dict.
        ledger_rows = _count_ledger_rows(tenant, db_value)
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "message": capture.last(),
            "ledger_rows": ledger_rows,
            "ledger_row": _read_ledger_row(tenant, db_value),
            "db_path": db_value,
            "port": server.port,
        }
    finally:
        # Always release the listening socket and its accept thread, even if
        # the child timed out or the caller inspects the result later.
        server.close()
        # The ledger row was written to the copy; drop the copy and its
        # directory.  ignore_errors makes a second attempt a no-op rather
        # than an exception, so an already-removed tree is not a failure.
        shutil.rmtree(pathlib.Path(db_value).parent, ignore_errors=True)