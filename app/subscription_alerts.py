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

All stubs raise ``NotImplementedError`` — implement after the RED phase tests
are committed.

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

from enum import Enum
from typing import Any

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


# ---------------------------------------------------------------------------
# Core functions (stubs)
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
        ISO date string of the next renewal.

    Raises
    ------
    NotImplementedError
        Stub — not yet implemented.
    """
    raise NotImplementedError(
        "extract_next_renewal_date not implemented yet"
    )


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

    Raises
    ------
    NotImplementedError
        Stub — not yet implemented.
    """
    raise NotImplementedError(
        "detect_price_increase not implemented yet"
    )


# ---------------------------------------------------------------------------
# Cancellation guides
# ---------------------------------------------------------------------------

CANCEL_GUIDES: dict[str, CancelGuide] = {}
"""Populated by the developer with the top 20 merchant cancellation guides."""

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

    Raises
    ------
    NotImplementedError
        Stub — not yet implemented.
    """
    raise NotImplementedError(
        "get_cancel_guide not implemented yet"
    )


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
    NotImplementedError
        Stub — not yet implemented.
    """
    raise NotImplementedError(
        "send_email_notification not implemented yet"
    )
