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
        logger.warning("SMTP notification failed: %s", exc)
        raise RuntimeError(f"SMTP notification failed: {exc}") from exc
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


def _build_scheduler_subscriptions(
    tenant: str = "demo",
) -> list[dict[str, Any]]:
    """Load subscription view-models from the accounting workspace.

    Falls back to :data:`DEMO_SUBSCRIPTIONS` when the accounting workspace
    has no recurring expenses for *tenant*.
    """
    from app.product_api import accounting as _accounting

    records = _accounting.recurring(tenant)
    subs: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        merchant = str(record.get("merchant") or "Unknown")
        occurrences = int(record.get("occurrences") or 0)
        last_date = str(record.get("last_date") or "")
        if not last_date:
            continue
        freq = _frequency_for(occurrences)
        renewal_date = extract_next_renewal_date(last_date, freq)
        amounts = [float(a) for a in (record.get("amounts") or [])]
        current = amounts[-1] if amounts else float(record.get("average_amount") or 0.0)
        baseline = amounts[-4:-1] if len(amounts) >= 2 else []
        subs.append(
            {
                "id": f"sub-{index:03d}",
                "merchant": merchant,
                "renewal_date": renewal_date,
                "amount": round(current, 2),
                "baseline": baseline,
                "email_alert_enabled": True,
            }
        )
    return subs if subs else list(DEMO_SUBSCRIPTIONS)


def _frequency_for(occurrences: int) -> Frequency:
    """Pick a recurrence frequency from the observed receipt count."""
    if occurrences >= 12:
        return Frequency.MONTHLY
    if occurrences >= 5:
        return Frequency.QUARTERLY
    return Frequency.ANNUAL


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
        ``price_emails_sent``, and ``date``.
    """
    anchor = _parse_today(today)

    if subscriptions is None:
        subscriptions = _build_scheduler_subscriptions(tenant)

    renewal_emails_sent = 0
    price_emails_sent = 0

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
            try:
                sent = send_email_notification(
                    subject, body, smtp_config=smtp_config
                )
                if sent:
                    price_emails_sent += 1
            except (OSError, RuntimeError):
                logger.warning(
                    "Failed to send price-hike email for %s", merchant
                )

    return {
        "subscriptions_checked": len(subscriptions),
        "renewal_emails_sent": renewal_emails_sent,
        "price_emails_sent": price_emails_sent,
        "date": anchor.isoformat(),
    }
