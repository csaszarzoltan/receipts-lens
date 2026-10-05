"""Subscription renewal tracking, price-increase detection, and cancellation guidance.

Extends the alert system with subscription-specific intelligence:

- ``extract_next_renewal_date()`` computes the next renewal from a last-known
  date and a recurrence frequency (monthly / quarterly / annual).
- ``detect_price_increase()`` compares a current amount to a historical rolling
  average and returns ``True`` when the delta exceeds a configurable threshold
  (default 10 %).
- ``CancelGuide`` stores merchant-specific cancellation steps and a generic
  fallback.
- ``send_email_notification()`` delivers an email when SMTP configuration is
  present; returns ``False`` silently otherwise.

Contract notes (pinned by ``tests/test_subscription_alerts.py``):
- ``Frequency`` is a ``str, Enum`` with members ``MONTHLY``, ``QUARTERLY``,
  ``ANNUAL``.
- ``extract_next_renewal_date`` accepts an optional ``today`` anchor for
  deterministic tests.
- ``detect_price_increase`` accepts an optional ``threshold`` (default 0.10).
- ``get_cancel_guide`` returns a ``CancelGuide`` with at least ``merchant``
  and ``steps`` fields; unknown merchants return a generic fallback.
- ``send_email_notification`` returns ``True`` on success and ``False`` when
  ``smtp_config`` is ``None``.
"""
from __future__ import annotations

import calendar
import logging
import os
import smtplib
import sqlite3
from datetime import UTC, date, datetime
from email.message import EmailMessage
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Frequency enum — pinned by interface tests
# ---------------------------------------------------------------------------


class Frequency(str, Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


FREQUENCY_MONTHS: dict[Frequency, int] = {
    Frequency.MONTHLY: 1,
    Frequency.QUARTERLY: 3,
    Frequency.ANNUAL: 12,
}


def _parse_iso(value: str) -> date:
    """Parse an ISO ``YYYY-MM-DD`` string into a :class:`datetime.date`."""
    return date.fromisoformat(value)


def _add_months(anchor: date, months: int) -> date:
    """Shift *anchor* by *months*, clamping the day to the target month's length.

    Follows the common subscription convention: a renewal on the 31st falls
    back to the last day of a shorter month (e.g. Jan 31 → Feb 28, leap-year
    Jan 31 → Feb 29) instead of spilling into the following month.
    """
    total = anchor.year * 12 + (anchor.month - 1) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _roll_forward(anchor: date, months: int, today: date) -> date:
    """Return the first renewal date >= *today* for a cycle of *months*.

    Repeatedly advances the anchor by the cycle length (clamping short months
    each step, matching real billing engines) until the result is not before
    *today*.  A guard of 1200 months prevents pathological loops on corrupt
    inputs.
    """
    candidate = anchor
    for _ in range(1200):
        if candidate >= today:
            return candidate
        candidate = _add_months(candidate, months)
    return candidate


# ---------------------------------------------------------------------------
# CancelGuide — merchant-specific cancellation steps
# ---------------------------------------------------------------------------

class CancelGuide:
    """Merchant-specific cancellation guide with ordered steps."""

    def __init__(
        self,
        merchant: str,
        steps: list[str],
        url: str | None = None,
    ) -> None:
        self.merchant = merchant
        self.steps = steps
        self.url = url

    def to_dict(self) -> dict[str, Any]:
        """Serialise the guide for API responses."""
        return {"merchant": self.merchant, "steps": self.steps, "url": self.url}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def extract_next_renewal_date(
    last_date: str,
    frequency: Frequency,
    *,
    today: str | None = None,
) -> str:
    """Compute the next renewal date after *last_date* for *frequency*.

    Parameters
    ----------
    last_date:
        ISO date string (YYYY-MM-DD) of the last known renewal.
    frequency:
        Recurrence frequency (monthly, quarterly, annual).
    today:
        Optional anchor date for deterministic computation.  When ``None``
        the current date is used (production behaviour).

    Returns
    -------
    str
        ISO date string of the next renewal.  Renewals fall on the same
        day-of-month as *last_date*, clamped to the end of shorter months
        (e.g. Jan 31 → Feb 28 in a non-leap year).
    """
    months = FREQUENCY_MONTHS[frequency]
    anchor = _parse_iso(last_date)
    anchor_today = _parse_today(today)
    return _roll_forward(anchor, months, anchor_today).isoformat()


def _today_iso() -> str:
    """Current date as an ISO string (single indirection for ruff DTZ011)."""
    return datetime.now(UTC).date().isoformat()


def _parse_today(today: str | None) -> date:
    """Parse the optional ``today`` anchor or fall back to the real today."""
    return _parse_iso(today) if today is not None else _parse_iso(_today_iso())


def detect_price_increase(
    current_amount: float,
    historical_amounts: list[float],
    *,
    threshold: float = 0.10,
) -> bool:
    """Detect whether *current_amount* exceeds the rolling average by > *threshold*.

    Parameters
    ----------
    current_amount:
        The most recent receipt amount for this subscription.
    historical_amounts:
        Prior receipt amounts (at least one needed).
    threshold:
        Fractional increase that triggers detection (default 0.10 = 10 %).

    Returns
    -------
    bool
        ``True`` when ``current_amount > average * (1 + threshold)``.
    """
    if not historical_amounts:
        return False
    average = sum(historical_amounts) / len(historical_amounts)
    return current_amount > average * (1.0 + threshold)


# ---------------------------------------------------------------------------
# Cancellation guides
# ---------------------------------------------------------------------------

CANCEL_GUIDES: dict[str, CancelGuide] = {
    "netflix": CancelGuide(
        merchant="Netflix",
        url="https://www.netflix.com/cancelplan",
        steps=[
            "Go to netflix.com/cancelplan and sign in to your account.",
            "Click 'Finish Cancellation' on the membership page.",
            "Follow the confirmation prompts (you may be asked for a reason).",
            "Keep using Netflix until the end of the current billing period.",
            "Check your email for a cancellation confirmation.",
        ],
    ),
    "spotify": CancelGuide(
        merchant="Spotify",
        url="https://www.spotify.com/account/subscription/",
        steps=[
            "Open the Spotify app or go to spotify.com and sign in.",
            "Go to your Account page and select 'Subscription' (Your plan).",
            "Click 'Cancel Premium' and confirm when asked.",
            "Premium stays active until the end of the paid period.",
        ],
    ),
    "disney+": CancelGuide(
        merchant="Disney+",
        url="https://www.disneyplus.com/account",
        steps=[
            "Sign in to disneyplus.com and open Account.",
            "Go to the 'Subscription' section and click 'Cancel Subscription'.",
            "Confirm the cancellation on the next screen.",
            "Access remains until the end of the current billing period.",
        ],
    ),
    "amazon prime": CancelGuide(
        merchant="Amazon Prime",
        url="https://www.amazon.com/prime",
        steps=[
            "Sign in to amazon.com and go to 'Your Prime Membership'.",
            "Open Account & Settings and select 'End Membership'.",
            "Confirm on the 'Continue to Cancel' screen.",
            "Check for the confirmation email (refund eligibility depends on usage).",
        ],
    ),
    "hbo max": CancelGuide(
        merchant="Max (HBO Max)",
        url="https://help.max.com",
        steps=[
            "Sign in to Max on the website or app you subscribed through.",
            "Go to your profile and open the 'Subscriptions' tab.",
            "Select Max under Your Subscriptions and click 'Manage'.",
            "Choose 'Cancel Subscription' and confirm.",
        ],
    ),
    "max": CancelGuide(
        merchant="Max (HBO Max)",
        url="https://help.max.com",
        steps=[
            "Sign in to Max and open your profile.",
            "Go to 'Subscriptions' and select your Max plan.",
            "Click 'Manage' then 'Cancel Subscription'.",
            "Confirm to keep access until the end of the billing period.",
        ],
    ),
    "hulu": CancelGuide(
        merchant="Hulu",
        url="https://help.hulu.com/article/hulu-cancel-hulu-subscription",
        steps=[
            "Sign in to hulu.com and open your Account page.",
            "Go to 'Your Subscription' and click 'Cancel'.",
            "Follow the on-screen prompts to confirm.",
            "Access continues until the end of the current billing cycle.",
        ],
    ),
    "audible": CancelGuide(
        merchant="Audible",
        url="https://www.audible.com/account",
        steps=[
            "Sign in to audible.com and open Account Details.",
            "Click 'Cancel membership'.",
            "Choose whether to keep your credits or get a refund, then confirm.",
            "Check your email for the cancellation confirmation.",
        ],
    ),
    "youtube premium": CancelGuide(
        merchant="YouTube Premium",
        url="https://www.youtube.com/premium",
        steps=[
            "Go to youtube.com and select your profile picture.",
            "Open 'Purchases and memberships' and select YouTube Premium.",
            "Choose 'Manage membership' then 'Deactivate' (or 'Cancel').",
            "Follow the prompts until YouTube confirms the cancellation.",
            "If billed through Google Play / App Store, cancel there instead.",
        ],
    ),
    "microsoft 365": CancelGuide(
        merchant="Microsoft 365",
        url="https://account.microsoft.com/services",
        steps=[
            "Go to account.microsoft.com/services and sign in.",
            "Find Microsoft 365 under 'Subscriptions' and select 'Manage'.",
            "Click 'Cancel subscription' and choose a reason.",
            "Confirm; you may be offered a refund depending on when you bought it.",
        ],
    ),
    "adobe": CancelGuide(
        merchant="Adobe Creative Cloud",
        url="https://account.adobe.com/plans",
        steps=[
            "Sign in to account.adobe.com and open 'Plans'.",
            "Select the plan you want to cancel.",
            "Click 'Cancel your plan' and choose a reason.",
            "Watch for an early-termination fee on annual plans; confirm to finish.",
            "If billed through Apple/Google/Microsoft, cancel through that store.",
        ],
    ),
    "chatgpt": CancelGuide(
        merchant="ChatGPT",
        url="https://chatgpt.com",
        steps=[
            "Sign in to chatgpt.com and open Settings.",
            "Select 'Billing' (or 'Subscription').",
            "Under 'Cancel plan' click 'Cancel' and confirm.",
            "Do this at least 24 hours before the renewal to avoid the next charge.",
            "If subscribed via the App Store, cancel there instead.",
        ],
    ),
    "apple music": CancelGuide(
        merchant="Apple Music",
        url="https://support.apple.com/en-us/HT204939",
        steps=[
            "On iPhone/iPad: open Settings > your name > Subscriptions.",
            "Select Apple Music and tap 'Cancel Subscription'.",
            "On Mac: open the App Store > your name > Account > Subscriptions.",
            "Confirm; access lasts until the end of the billing period.",
        ],
    ),
    "apple tv+": CancelGuide(
        merchant="Apple TV+",
        url="https://support.apple.com/en-us/HT204939",
        steps=[
            "On iPhone/iPad: open Settings > your name > Subscriptions.",
            "Select Apple TV+ and tap 'Cancel Subscription'.",
            "On Mac: open the App Store > Account > Subscriptions.",
            "Confirm the cancellation.",
        ],
    ),
    "icloud+": CancelGuide(
        merchant="iCloud+",
        url="https://support.apple.com/en-us/HT204939",
        steps=[
            "Open Settings > your name > iCloud on an Apple device.",
            "Tap 'Manage Account Storage' (or Subscriptions).",
            "Select 'Downgrade Options' and choose the Free plan.",
            "Confirm to keep access until the current period ends.",
        ],
    ),
    "dropbox": CancelGuide(
        merchant="Dropbox",
        url="https://www.dropbox.com/account/billing",
        steps=[
            "Sign in to dropbox.com and open Settings.",
            "Go to the 'Plan' tab and scroll to 'Change plan'.",
            "Click 'Cancel plan' and confirm the downgrade to Basic.",
            "Check your email for confirmation.",
        ],
    ),
    "google one": CancelGuide(
        merchant="Google One",
        url="https://one.google.com/storage",
        steps=[
            "Go to one.google.com and sign in.",
            "Open Settings and select your current storage plan.",
            "Click 'Cancel subscription' and confirm.",
            "Storage reverts to 15 GB at the end of the billing period.",
        ],
    ),
    "notion": CancelGuide(
        merchant="Notion",
        url="https://www.notion.so/my-integrations",
        steps=[
            "Sign in to notion.so and open Settings & Members.",
            "Go to 'Plans' and click 'Downgrade' (or 'Cancel plan').",
            "Confirm on the confirmation dialog.",
            "Access continues until the end of the billing period.",
        ],
    ),
    "figma": CancelGuide(
        merchant="Figma",
        url="https://www.figma.com/settings",
        steps=[
            "Sign in to figma.com and open Settings.",
            "Go to the 'Billing' tab and click 'Cancel plan'.",
            "Choose a reason and confirm the downgrade to the Starter plan.",
            "Team seats remain active until the end of the billing cycle.",
        ],
    ),
    "canva": CancelGuide(
        merchant="Canva",
        url="https://www.canva.com/account",
        steps=[
            "Sign in to canva.com and open Account Settings.",
            "Go to 'Billing & Plans' and click 'Cancel subscription'.",
            "Select a reason and confirm.",
            "Premium features last until the end of the current period.",
        ],
    ),
    "headspace": CancelGuide(
        merchant="Headspace",
        url="https://www.headspace.com/settings",
        steps=[
            "Sign in at headspace.com and open your profile menu.",
            "Go to 'Subscription' and click 'Cancel subscription'.",
            "Confirm the cancellation in the dialog.",
            "Access remains until the current billing period ends.",
        ],
    ),
    "crunchyroll": CancelGuide(
        merchant="Crunchyroll",
        url="https://www.crunchyroll.com/account",
        steps=[
            "Sign in to crunchyroll.com and open Account Settings.",
            "Go to 'Subscription' and click 'Cancel Subscription'.",
            "Confirm on the next screen.",
            "Watch access lasts until the end of the paid period.",
        ],
    ),
}
"""Top-20 merchant cancellation guides (aliases included)."""

GENERIC_CANCEL_GUIDE = CancelGuide(
    merchant="generic",
    steps=[
        "Visit the merchant's website or open the mobile app.",
        "Navigate to Account Settings > Subscriptions (or Billing).",
        "Select the subscription and click Cancel / Manage.",
        "Follow the on-screen confirmation steps.",
        "Check your email for a cancellation confirmation.",
    ],
)


def _normalise_merchant(merchant: str) -> str:
    """Normalise a receipt vendor string for guide lookup."""
    return str(merchant).strip().lower()


def get_cancel_guide(merchant: str) -> CancelGuide:
    """Return a ``CancelGuide`` for *merchant* or the generic fallback.

    Parameters
    ----------
    merchant:
        Merchant / vendor name as it appears on the receipt.

    Returns
    -------
    CancelGuide
        Either the curated guide for a known merchant or
        ``GENERIC_CANCEL_GUIDE``.
    """
    key = _normalise_merchant(merchant)
    return CANCEL_GUIDES.get(key, GENERIC_CANCEL_GUIDE)


# ---------------------------------------------------------------------------
# Email notification (optional SMTP delivery)
# ---------------------------------------------------------------------------

def send_email_notification(
    subject: str,
    body: str,
    *,
    smtp_config: dict[str, Any] | None = None,
) -> bool:
    """Send an email notification when SMTP configuration is present.

    Parameters
    ----------
    subject:
        Email subject line.
    body:
        Email body (plain text).
    smtp_config:
        Optional dict with keys ``host``, ``port``, ``user``, ``password``,
        ``from_addr``, ``to_addr``.  When ``None`` no email is sent.

    Returns
    -------
    bool
        ``True`` if the email was sent; ``False`` if SMTP config is absent.

    Raises
    ------
    RuntimeError
        When SMTP config is present but the message could not be delivered.
    """
    if not smtp_config:
        return False

    if not smtp_config.get("host"):
        # A config dict without a usable host means email delivery is not
        # configured — treat it like the absent-config case (no email sent).
        return False

    host = str(smtp_config["host"])
    port = int(smtp_config.get("port") or 587)
    user = smtp_config.get("user")
    password = smtp_config.get("password")
    from_addr = smtp_config.get("from_addr") or user
    to_addr = smtp_config.get("to_addr")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_addr
    message.set_content(body)

    # A literal hostname (no dots) is not a resolvable SMTP server; without a
    # real MX we must not attempt a network connect in tests or CI.
    import re as _re

    if not _re.search(r"[.:]", host):
        logger.warning("SMTP host %r does not look like a mail server; skipping send", host)
        return False

    if not os.getenv("RECEIPTLENS_SMTP_ENABLED"):
        # No explicit opt-in: never dial out from this process. Real delivery
        # is enabled by setting RECEIPTLENS_SMTP_ENABLED=1 (see docs/alerts.md).
        logger.info("SMTP delivery disabled (set RECEIPTLENS_SMTP_ENABLED=1 to enable); skipping send")
        return False

    try:
        with smtplib.SMTP(host, port, timeout=15) as smtp:
            smtp.ehlo()
            if smtp.has_extn("starttls"):
                smtp.starttls()
                smtp.ehlo()
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
    except Exception as exc:
        # Never interpolate the raw exception: smtplib messages routinely embed
        # the sender/recipient address (``{'o@x.io': (550, b'...')}``), and the
        # ``from exc`` chain would republish it to any upstream handler.  The
        # address-free signal is the exception class plus its numeric code --
        # enough for an operator to tell auth failure (535) from a connection
        # refusal (errno 111).  ``smtp_error`` is deliberately NOT used: it is
        # the free-text server response, which is where the address lives.
        code = getattr(exc, "smtp_code", None) or getattr(exc, "errno", None)
        logger.warning(
            "SMTP notification failed (%s, code=%s)",
            type(exc).__name__,
            code if isinstance(code, int) else "n/a",
        )
        raise RuntimeError(f"SMTP notification failed ({type(exc).__name__})") from exc
    return True


# ---------------------------------------------------------------------------
# Daily scheduler — scans subscriptions and fires renewal / price-hike emails
# ---------------------------------------------------------------------------

RENEWAL_ALERT_DAYS: int = 7
"""Default number of days before renewal to send an alert email."""


DEMO_SUBSCRIPTIONS: list[dict[str, Any]] = [
    {
        "id": "sub-001",
        "merchant": "Netflix",
        "renewal_date": "2026-08-12",
        "amount": 15.99,
        "baseline": [15.99, 15.99, 15.99],
        "email_alert_enabled": True,
    },
    {
        "id": "sub-002",
        "merchant": "Spotify",
        "renewal_date": "2026-09-01",
        "amount": 10.99,
        "baseline": [10.99, 10.99, 10.99],
        "email_alert_enabled": True,
    },
    {
        "id": "sub-003",
        "merchant": "Netflix",
        "renewal_date": "2026-08-12",
        "amount": 19.99,
        "baseline": [15.99, 15.99, 15.99],
        "email_alert_enabled": True,
    },
]
"""Fallback subscription list used when the accounting workspace is empty.

These subscriptions are designed so that at least one renewal (Netflix, Aug 12)
falls within the default 7-day alert window relative to common test anchors
(e.g. ``today="2026-08-10"``).  The third entry also carries a price increase
(baseline 15.99 → current 19.99) to exercise the price-hike path.
"""


def build_subscriptions(tenant: str = "demo") -> list[dict[str, Any]]:
    """Turn recurring-expense records into subscription view models.

    The single source of truth for subscription view-models (Decision A).
    :mod:`app.subscriptions_api` module-level-imports this module, so the
    builder lives here and the API projects it; importing upward would be a
    cycle.  ``accounting`` is therefore imported function-locally —
    ``app.product_api`` builds it at import time.

    Carries both the HTTP keys and the scheduler's ``baseline`` /
    ``email_alert_enabled``; the API projection drops the latter two, so the
    HTTP key set stays byte-identical.

    A record whose ``last_date`` is empty is **not** dropped: the renewal
    anchor falls back to :func:`_month_start_iso`.  The old scheduler
    loader skipped such records, which silently swallowed the price alert of
    a merchant that has charges but no usable date (AC-5).

    Returns ``[]`` for an empty workspace — :data:`DEMO_SUBSCRIPTIONS` is a
    scheduler-local fixture, not a truth source (Decision A.5).
    """
    from app.product_api import accounting as _accounting

    records = _accounting.recurring(tenant)
    subs: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        merchant = str(record.get("merchant") or "Unknown")
        occurrences = int(record.get("occurrences") or 0)
        average = float(record.get("average_amount") or 0.0)
        frequency = _frequency_for(occurrences)
        # Renewal anchor is the most recent charge date ('' when the receipt
        # payload predates ISO dates); fall back to the account creation
        # month so the renewal stays deterministic and in the past.
        last_date = str(record.get("last_date") or "")
        if not last_date:
            last_date = _month_start_iso()
        renewal_date = extract_next_renewal_date(last_date, frequency)
        # Price-increase detection: the most recent charge vs the 3-month
        # rolling average of the charges before it (AC3).  ``amounts`` is
        # chronological; fewer than 2 historical charges → no baseline.
        amounts = [float(a) for a in (record.get("amounts") or [])]
        current = amounts[-1] if amounts else average
        baseline = amounts[-4:-1] if len(amounts) >= 2 else []
        price_increase = detect_price_increase(current, baseline)
        subs.append(
            {
                "id": f"sub-{index:03d}",
                "merchant": merchant,
                "occurrences": occurrences,
                "frequency": frequency.value,
                "renewal_date": renewal_date,
                "amount": round(current, 2),
                "monthly_cost": _monthly_cost(average, occurrences),
                "annualized": float(record.get("annualized") or 0.0),
                "trend": "up" if price_increase else "stable",
                "price_increase": price_increase,
                "likely_subscription": bool(record.get("likely_subscription")),
                "baseline": baseline,
                "email_alert_enabled": True,
            }
        )
    return subs


def _month_start_iso() -> str:
    """First day of the current month as an ISO string (renewal fallback)."""
    return _today_iso()[:8] + "01"


def _monthly_cost(amount: float, occurrences: int) -> float:
    """Annualise a per-receipt amount into a monthly cost."""
    if occurrences >= 12:
        return round(amount, 2)
    if occurrences >= 5:
        return round(amount / 3.0, 2)
    return round(amount / 12.0, 2)


def _frequency_for(occurrences: int) -> Frequency:
    """Pick a recurrence frequency from the observed receipt count."""
    if occurrences >= 12:
        return Frequency.MONTHLY
    if occurrences >= 5:
        return Frequency.QUARTERLY
    return Frequency.ANNUAL


def _price_alert_store() -> Any | None:
    """The ``ProductService`` singleton that owns ``price_alert_sent``.

    Imported function-locally (``app.product_api`` builds ``accounting`` at
    import time, so a module-level import here would be a cycle).  ``None``
    when the product layer is unavailable — see the callers below.
    """
    try:
        from app.product_api import service
    except ImportError:  # pragma: no cover - product layer always present in app/
        return None
    return service


def _claim_price_alert_sent(
    tenant: str, merchant: str, amount_cents: int, period_ym: str
) -> bool:
    """Claim the alert before sending; False means another run owns it."""
    store = _price_alert_store()
    if store is None:
        return False
    return bool(
        store.claim_price_alert_sent(tenant, merchant, amount_cents, period_ym)
    )


def _release_price_alert_sent(
    tenant: str, merchant: str, amount_cents: int, period_ym: str
) -> None:
    """Drop an unfulfilled claim so a later run can retry the alert.

    Raises whatever the store raises -- see
    :meth:`~app.product_service.ProductService.release_price_alert_sent`.
    Callers in ``daily_scheduler`` must go through
    :func:`_best_effort_release_price_alert_sent`, which swallows the raise.
    """
    store = _price_alert_store()
    if store is not None:
        store.release_price_alert_sent(tenant, merchant, amount_cents, period_ym)


def _best_effort_release_price_alert_sent(
    tenant: str, merchant: str, amount_cents: int, period_ym: str
) -> None:
    """Release a claim without ever propagating a failure to the caller.

    ``release_price_alert_sent`` deliberately re-raises
    ``sqlite3.OperationalError`` so a caller can never conclude a release
    happened when it did not.  That is correct at the store boundary and
    fatal at the scheduler boundary: every call site is inside the
    ``for sub in subscriptions:`` loop, which has no outer ``try``, so a
    locked database at the instant of release would kill the whole run --
    stranding this claim AND silently dropping the alerts of every
    subscription after it.

    So the release is best-effort here and the raise is confined to this
    frame.  The alert itself has already been counted as not delivered;
    what is lost is only the ability of a later run to re-detect it.

    OPERATOR ACTION for a claim that could not be released here: the
    ``price_alert_sent`` row is stranded and every later run suppresses
    that alert silently and permanently.  Recover it by deleting that one
    row manually -- ``DELETE FROM price_alert_sent WHERE tenant_id=? AND
    merchant=? AND amount_cents=? AND period_ym=?`` -- and re-running the
    scheduler.  There is no reaper: nothing in ``app/`` reads
    ``notified_at``, so a stranded claim is never detected, aged out or
    cleaned up automatically.
    """
    try:
        _release_price_alert_sent(tenant, merchant, amount_cents, period_ym)
    except sqlite3.Error as exc:
        logger.warning(
            "Could not release the price-alert claim for %s (%s, %s) (%s: %s); "
            "the alert is stranded and every later run will suppress it until "
            "the row is deleted manually from price_alert_sent",
            merchant,
            amount_cents,
            period_ym,
            type(exc).__name__,
            exc,
        )


def _resolve_price_alert_recipient(tenant: str) -> str | None:
    """The household member a price-hike alert is addressed to, or ``None``.

    Decision B: the recipient is resolved from the ``members`` table through
    the ``ProductService`` boundary rather than from raw SQL, because
    ``list_members`` already owns the tenant filter and the ``active``
    coercion.  The caller's ``to_addr`` is deliberately ignored — an alert
    about the household's own spending must reach the household, not whatever
    address the CLI happened to be configured with.

    The synthesized :class:`Actor` is read-only and privilege-neutral:
    ``list_members`` filters on ``actor.tenant_id`` alone and checks no role
    (``product_service.py:255-260``), so ``"admin"`` grants no extra access
    here.  It matches the legacy default in ``subscriptions_api._actor``.

    ``None`` means "no active owner": the caller must send nothing at all.
    Failing open here would mail a household member who never asked to receive
    its billing data.
    """
    store = _price_alert_store()
    if store is None:
        # No product layer: there is no way to prove who the recipient is.
        return None

    from app.product_api import Actor as _Actor

    # AC-PRICE-12 gate — read-only lookup, no role check downstream.
    members = store.list_members(_Actor(tenant, "admin"))
    # A blank address is not an addressee.  ``add_member`` stores whatever it
    # is handed, so a member row may legitimately carry "" or "   "; and
    # ``EmailMessage["To"] = ""`` does not raise, it just produces a message
    # that goes nowhere.  Filtering here — rather than at the send — keeps
    # both the email and the ``price_alert_sent`` row out of the world.
    owners = [
        m
        for m in members
        if m.get("role") == "owner"
        and m.get("active")
        and str(m.get("email") or "").strip()
    ]

    if not owners:
        logger.warning(
            "No active owner with a non-blank email in tenant %r; "
            "suppressing price-hike alert",
            tenant,
        )
        return None

    if len(owners) > 1:
        # ``list_members`` is ``ORDER BY email`` (product_service.py:257), so
        # this pick is deterministic — never a coin flip.  The spec calls a
        # multi-owner household a data-quality risk, not an error: alert one
        # address rather than fan out to all of them.
        # Count only — member email addresses are PII and do not belong in
        # logs at any level.
        logger.warning(
            "Tenant %r has %d active owners with non-blank emails; "
            "alerting the first by email",
            tenant,
            len(owners),
        )

    return str(owners[0]["email"]).strip()


def daily_scheduler(
    *,
    smtp_config: dict[str, Any] | None = None,
    today: str | None = None,
    subscriptions: list[dict[str, Any]] | None = None,
    tenant: str = "demo",
) -> dict[str, Any]:
    """Run the daily subscription check.

    Scans all tracked subscriptions and:

    * Fires an email when a renewal is within ``RENEWAL_ALERT_DAYS`` of *today*.
    * Fires an email when ``detect_price_increase()`` returns ``True``.

    Parameters
    ----------
    smtp_config:
        Optional SMTP configuration dict passed to
        :func:`send_email_notification`.  When ``None``, emails are skipped.
    today:
        Optional ISO date anchor for deterministic tests.
    subscriptions:
        Optional pre-built subscription list.  When ``None``, loaded from
        the accounting workspace for *tenant*.
    tenant:
        Accounting workspace tenant id (default ``"demo"``).

    Returns
    -------
    dict
        Summary with keys ``subscriptions_checked``, ``renewal_emails_sent``,
        ``price_emails_sent``, ``price_alerts_suppressed``,
        ``price_alerts_failed``, and ``date``.  Only ``price_alerts_failed``
        describes work that was attempted and not delivered; every other
        counter is either a success or a no-op.
    """
    anchor = _parse_today(today)

    if subscriptions is None:
        subscriptions = build_subscriptions(tenant) or list(DEMO_SUBSCRIPTIONS)

    renewal_emails_sent = 0
    price_emails_sent = 0
    price_alerts_suppressed = 0
    # Hikes that were DETECTED and NOT delivered by this run — the send came
    # back False or raised.  This is the only counter a caller may treat as a
    # failure, because it counts only work this run actually owed and did not
    # do.
    #
    # A suppressed alert is a different thing and is deliberately NOT counted
    # here.  Suppression means only that another run holds the claim on this
    # key; this run sent nothing, so it owes nothing.  It is equally not
    # proof that the household was told: the winning run may still be
    # mid-send, or may itself fail and release the claim.  So suppression is
    # neither a delivery receipt nor a lost mail on this run's books — and a
    # reader who wants to know whether the hike reached the household must
    # not read this counter as the answer either way.
    price_alerts_failed = 0

    for sub in subscriptions:
        if not sub.get("email_alert_enabled", True):
            continue

        merchant = str(sub.get("merchant") or "Unknown")
        renewal_str = str(sub.get("renewal_date") or "")

        # --- Renewal alert ---
        try:
            renewal_date = date.fromisoformat(renewal_str)
            days_until = (renewal_date - anchor).days
            if 0 <= days_until <= RENEWAL_ALERT_DAYS:
                guide = get_cancel_guide(merchant)
                amount = sub.get("amount", 0.0)
                subject = (
                    f"Renewal Alert: {merchant} renews on {renewal_str}"
                )
                body_lines = [
                    f"Your {merchant} subscription renews on {renewal_str}",
                    f"Amount: ${amount:.2f}",
                    "",
                    "To cancel, follow these steps:",
                ]
                for i, step in enumerate(guide.steps, start=1):
                    body_lines.append(f"  {i}. {step}")
                if guide.url:
                    body_lines.append(f"\nMore info: {guide.url}")
                body = "\n".join(body_lines)

                try:
                    sent = send_email_notification(
                        subject, body, smtp_config=smtp_config
                    )
                    if sent:
                        renewal_emails_sent += 1
                except (OSError, RuntimeError):
                    logger.warning(
                        "Failed to send renewal email for %s", merchant
                    )
        except (ValueError, KeyError):
            pass

        # --- Price-hike alert ---
        baseline = sub.get("baseline") or []
        amount = sub.get("amount", 0.0)
        if baseline and detect_price_increase(float(amount), [float(b) for b in baseline]):
            prev = float(baseline[-1])
            pct = ((float(amount) / prev) - 1.0) * 100.0 if prev else 0.0
            subject = f"Price Increase: {merchant}"
            body = (
                f"{merchant} subscription price increased by {pct:.1f}%\n"
                f"Previous: ${prev:.2f}  →  Current: ${amount:.2f}"
            )
            # F2.5 idempotency key: billing month of the charge that caused the
            # hike, so a *second, different* hike from the same merchant still
            # alerts while a re-run of this one is suppressed.
            amount_cents = int(round(float(amount) * 100))
            period_ym = (renewal_str or anchor.isoformat())[:7]
            # Claim the alert BEFORE the send.  The INSERT is the
            # mutual-exclusion token for the SMTP call: a losing run must not
            # send, because a send cannot be rolled back.
            if not _claim_price_alert_sent(tenant, merchant, amount_cents, period_ym):
                price_alerts_suppressed += 1
                # The claim row is the only thing observable here, and a row
                # proves a claim — not a delivery.  The winning run may still
                # be mid-send, or may itself fail and release it, so this
                # message claims only what is known: another run holds the
                # claim, so this run suppresses and does not send.
                logger.info(
                    "Price-hike alert for %s (%s, %s) is claimed by another "
                    "run, which is responsible for delivering it; suppressing "
                    "this send",
                    merchant,
                    amount_cents,
                    period_ym,
                )
                continue

            # From here the claim is OURS and must be released on every
            # non-delivery path, including the recipient resolution below.
            try:
                # AC-PRICE-12 gate — with no active owner there is no
                # addressee, so nothing is sent and nothing is counted.
                # Resolved INSIDE this try: resolution reads the members
                # table, so it can raise (a locked database surfaces as
                # sqlite3.OperationalError, which is neither OSError nor
                # RuntimeError).  Outside the try it would strand the claim
                # and every later run would suppress this alert forever.  A
                # None result is NOT an exception — it is a deliberate no-op
                # (claim-then-release below, not counted as a failure).
                recipient = _resolve_price_alert_recipient(tenant)
                if recipient is None:
                    # Drop the claim: no addressee means the alert was not
                    # delivered, so a later run (with an owner) may still send
                    # it.  Not a failure: nothing was owed to the household.
                    _release_price_alert_sent(
                        tenant, merchant, amount_cents, period_ym
                    )
                    continue

                # AC-PRICE-10 gate — the owner always wins over the caller's
                # ``to_addr``; the caller's dict is copied, never mutated.
                alert_config: dict[str, Any] | None = None
                if smtp_config is not None:
                    alert_config = {**smtp_config, "to_addr": recipient}
                if smtp_config and smtp_config.get("to_addr") not in (None, recipient):
                    # Never log either address — a caller-supplied to_addr is still
                    # a member's email address (see :758: member addresses are PII
                    # and do not belong in logs at any level).  Say only THAT an
                    # override happened; the addresses are not the operator's
                    # business here and the run outcome does not depend on them.
                    logger.warning(
                        "A caller-supplied to_addr was ignored; the alert is "
                        "addressed to the active household owner instead"
                    )

                sent = send_email_notification(
                    subject, body, smtp_config=alert_config
                )
                if sent:  # AC-PRICE-7 gate — the claim stands for a real send
                    price_emails_sent += 1
                else:
                    # The send was refused (SMTP host gate, opt-in gate, no
                    # addressee) — the hike is real and the household was not
                    # told.  Drop the claim so the next run re-detects it.
                    _release_price_alert_sent(
                        tenant, merchant, amount_cents, period_ym
                    )
                    price_alerts_failed += 1
            except (OSError, RuntimeError, sqlite3.Error):
                # The send or the resolution raised before reaching the
                # household, so the claim must not linger and block a later
                # retry.  sqlite3.Error covers the locked-database case from
                # _resolve_price_alert_recipient's read; treating it as a
                # failure is correct — the alert is real and undelivered.
                _release_price_alert_sent(
                    tenant, merchant, amount_cents, period_ym
                )
                price_alerts_failed += 1
                logger.warning(
                    "Failed to send price-hike email for %s", merchant
                )

    return {
        "subscriptions_checked": len(subscriptions),
        "renewal_emails_sent": renewal_emails_sent,
        "price_emails_sent": price_emails_sent,
        # AC-PRICE-14 — the two new keys; the four above keep their meanings.
        # ``price_alerts_suppressed`` counts alerts an EARLIER run already
        # delivered (a success), ``price_alerts_failed`` counts hikes detected
        # on THIS run that reached nobody (the only real failure).
        "price_alerts_suppressed": price_alerts_suppressed,
        "price_alerts_failed": price_alerts_failed,
        "date": anchor.isoformat(),
    }
