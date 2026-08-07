#!/usr/bin/env python3
"""Execute the documented Python API example against the real library."""
import sys

# From the documented example:
from app.subscription_alerts import (
    Frequency,
    detect_price_increase,
    extract_next_renewal_date,
    get_cancel_guide,
    send_email_notification,
)

# Next renewal date (monthly, quarterly, annual)
r1 = extract_next_renewal_date("2026-07-15", Frequency.MONTHLY)
print("renewal monthly:", r1, "-> expect 2026-08-15")

# Price-increase detection (>10% over the rolling average by default)
r2 = detect_price_increase(12.99, [9.99, 9.99, 9.99])
print("price increase:", r2, "-> expect True")

# Cancellation guide (curated or generic fallback)
guide = get_cancel_guide("Netflix")
print("guide.merchant:", guide.merchant)
print("guide.steps count:", len(guide.steps))
print("guide.to_dict():", guide.to_dict())

# Email notification (no SMTP config -> False, no network attempt)
r3 = send_email_notification("Subject", "Body")
print("send_email_notification no config:", r3, "-> expect False")

# Generic fallback for unknown merchant
g2 = get_cancel_guide("Some Unknown Shop")
print("generic fallback:", g2.merchant, g2.url, len(g2.steps))

# Deterministic merchant resolution for unresolvable ids (from subscriptions_api)
from app.subscriptions_api import _merchant_from_id

print("_merchant_from_id('sub-002'):", _merchant_from_id("sub-002"))
print("_merchant_from_id('zzz'):", _merchant_from_id("zzz"))

# AlertStore methods exist
from app.alerts import AlertStore

store = AlertStore()
print("AlertStore has schedule_renewal_alerts:", hasattr(store, "schedule_renewal_alerts"))
print("AlertStore has create_price_increase_alert:", hasattr(store, "create_price_increase_alert"))
