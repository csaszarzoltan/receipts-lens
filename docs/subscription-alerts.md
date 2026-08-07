# Subscription Alerts & Cancellation Guides

ReceiptLens detects your recurring expenses and turns them into a **subscription
view**: next renewal date, monthly cost, price-increase detection, and
merchant-specific **cancellation guides** so you can act before the next charge.

Implementation: `app/subscription_alerts.py` (renewal math, price detection,
cancel guides, SMTP notification), `app/subscriptions_api.py` (REST endpoints),
`app/alerts.py` (`SUBSCRIPTION_RENEWAL` / `PRICE_INCREASE` alert types),
`frontend/app/(app)/subscriptions/page.tsx` (Subscriptions UI).

## How subscriptions are detected

Subscriptions are derived from the recurring-expense analysis
(`AccountingWorkspace.recurring()` in `app/accounting_workspace.py`):

- A merchant becomes a subscription candidate after **at least 2 receipts** with
  the same vendor are stored.
- The recurrence frequency is inferred from how many charges were observed:

  | Occurrences | Frequency |
  |---|---|
  | 12+ | `monthly` |
  | 5–11 | `quarterly` |
  | 2–4 | `annual` |

- The **next renewal date** is computed from the most recent charge date,
  rolled forward to the first date on or after today (day-of-month is clamped
  for short months — Jan 31 renews on Feb 28).
- **Price-increase detection** compares the most recent charge against the
  rolling average of the preceding charges. A charge more than **10% above the
  baseline** (default threshold) flags the subscription as `price_increase:
  true` with `trend: "up"`. A recent jump also typically fails the
  recurring-expense variance check, so a flagged subscription often reports
  `likely_subscription: false` — the trend is reported regardless.

> Detection needs **matching merchant names** across receipts. OCR variations
> (e.g. "Netflix.com" vs "Netflix") will split the merchant into two groups.

## REST endpoints

### `GET /api/v1/subscriptions`

List active subscriptions with renewal dates, monthly cost, and price trend.

```bash
curl http://localhost:8000/api/v1/subscriptions
```

Response:

```json
{
  "subscriptions": [
    {
      "id": "sub-001",
      "merchant": "Spotify",
      "occurrences": 6,
      "frequency": "quarterly",
      "renewal_date": "2026-11-03",
      "amount": 10.99,
      "monthly_cost": 3.66,
      "annualized": 131.88,
      "trend": "stable",
      "price_increase": false,
      "likely_subscription": true
    },
    {
      "id": "sub-002",
      "merchant": "Netflix",
      "occurrences": 6,
      "frequency": "quarterly",
      "renewal_date": "2026-09-15",
      "amount": 12.99,
      "monthly_cost": 3.5,
      "annualized": 125.88,
      "trend": "up",
      "price_increase": true,
      "likely_subscription": false
    }
  ],
  "summary": {
    "total": 2,
    "monthly_total": 7.16
  }
}
```

> Ids are assigned per request, ordered by annualized spend descending; the
> renewal dates and amounts above reflect the stored receipts at capture time.
> Renewal dates roll forward to the current date, so they shift as new charges
> arrive. A merchant with a price increase usually fails the recurring-expense
> variance check, which is why `likely_subscription` can be `false` for a
> flagged subscription (the trend is still reported).

| Field | Description |
|---|---|
| `id` | Stable per-request id (`sub-001`, `sub-002`, …), ordered by annualized cost descending |
| `merchant` | Vendor name as detected from receipts |
| `occurrences` | Number of stored receipts for this merchant |
| `frequency` | `monthly` \| `quarterly` \| `annual` (inferred from occurrences) |
| `renewal_date` | Next renewal date (ISO `YYYY-MM-DD`) |
| `amount` | Most recent charge amount |
| `monthly_cost` | Annualized cost normalized to a monthly figure |
| `annualized` | Average charge × 12 |
| `trend` | `up` when a price increase was detected, else `stable` |
| `price_increase` | Boolean; `true` when the latest charge exceeds the rolling average by more than 10% |
| `likely_subscription` | Boolean from the recurring-expense analysis (variance check, overridable via recurring-expense feedback) |

### `GET /api/v1/subscriptions/{id}/cancel-guide`

Return merchant-specific cancellation steps for a subscription. Known
merchants (Netflix, Spotify, Disney+, Amazon Prime, Max, Hulu, Audible,
YouTube Premium, Microsoft 365, Adobe, ChatGPT, Apple Music/TV+/iCloud+,
Dropbox, Google One, Notion, Figma, Canva, Headspace, Crunchyroll, …) get
curated steps and a link to the merchant's account page; anything else falls
back to a generic guide.

```bash
curl http://localhost:8000/api/v1/subscriptions/sub-002/cancel-guide
```

Response:

```json
{
  "subscription_id": "sub-002",
  "merchant": "Netflix",
  "steps": [
    "Go to netflix.com/cancelplan and sign in to your account.",
    "Click 'Finish Cancellation' on the membership page.",
    "Follow the confirmation prompts (you may be asked for a reason).",
    "Keep using Netflix until the end of the current billing period.",
    "Check your email for a cancellation confirmation."
  ],
  "url": "https://www.netflix.com/cancelplan"
}
```

Unknown merchants (or unresolvable ids) return the generic guide with
`"url": null` and `"merchant": "generic"`.

Both endpoints accept the tenant/role headers used across the product
workspace (`x-tenant-id` defaults to `demo`, `x-role` to `admin`).

## Email alerts

Renewal and price-increase notifications can be delivered by email. Delivery
is **off by default**: the SMTP path only dials out when both a usable SMTP
configuration is provided **and** `RECEIPTLENS_SMTP_ENABLED=1` is set (the env
gate prevents the process from ever connecting to a mail server implicitly).

| Variable | Default | Description |
|---|---|---|
| `RECEIPTLENS_SMTP_ENABLED` | *(off)* | Set to `1` to allow SMTP delivery. The gate is checked first — without it the process never dials out. |

SMTP connection settings are **not** read from environment variables; they are
passed as a dict to `send_email_notification(smtp_config=...)` with the keys
`host` / `port` / `user` / `password` / `from_addr` / `to_addr` (port defaults
to `587` when omitted, `from_addr` falls back to `user`, and STARTTLS is
attempted when the server advertises it). Delivery is best-effort: with no
config, no host, or the env gate off it returns `False` silently; with config
present but a failed send it raises `RuntimeError`.

The Subscriptions UI exposes an **Email alerts** toggle. The preference is
persisted via the product preferences API and survives restarts:

```bash
curl -X PUT http://localhost:8000/product/preferences \
  -H "x-tenant-id: demo" -H "Content-Type: application/json" \
  -d '{"payload": {"email_alerts": true}}'
```

## Alert types

`app/alerts.py` adds two alert types to the existing alert store:

- **`SUBSCRIPTION_RENEWAL`** (severity `info`) — created by
  `AlertStore.schedule_renewal_alerts(subscriptions, days_before=3)`: fires
  when a renewal is `0..days_before` days away.
- **`PRICE_INCREASE`** (severity `warning`) — created by
  `AlertStore.create_price_increase_alert(merchant, current_amount,
  previous_amount)`: reports the percentage increase and the old/new amounts.

The alert store itself is in-memory (same as the budget alerts); the
subscription endpoints and the UI surface the detection directly, so the
alert types are available for consumers that call the store — they are not
automatically generated on every request.

## Python API

`app/subscription_alerts.py` is importable as a library:

```python
from app.subscription_alerts import (
    Frequency,
    detect_price_increase,
    extract_next_renewal_date,
    get_cancel_guide,
    send_email_notification,
)

# Next renewal date (monthly, quarterly, annual)
extract_next_renewal_date("2026-07-15", Frequency.MONTHLY)
# -> "2026-08-15"  (pass today="YYYY-MM-DD" for deterministic computation)

# Price-increase detection (>10% over the rolling average by default)
detect_price_increase(12.99, [9.99, 9.99, 9.99])
# -> True

# Cancellation guide (curated or generic fallback)
guide = get_cancel_guide("Netflix")
guide.merchant  # -> "Netflix"
guide.steps     # -> list[str]
guide.to_dict() # -> {"merchant": ..., "steps": [...], "url": ...}

# Email notification (no SMTP config -> False, no network attempt)
send_email_notification("Subject", "Body")
# -> False
```

See [examples/subscriptions.py](../examples/subscriptions.py) for a runnable
end-to-end example against a live server.

## Subscriptions UI

The Subscriptions page (frontend route `subscriptions`) shows:

- **Summary cards** — active subscription count and total monthly cost.
- **Upcoming renewals** — subscriptions renewing within 14 days, sorted by
  date, with a "renews today / tomorrow / in N days" badge.
- **Price changes** — subscriptions flagged as `price_increase`, with the
  current amount and monthly cost.
- **All subscriptions table** — merchant, frequency, renewal date, monthly
  and annualized cost, trend (`↑ up` / `→ stable`), and a **Cancel guide**
  button that opens the merchant's cancellation steps in a modal (with a link
  to the merchant account page when available).
- **Email alerts toggle** — persisted through `PUT /product/preferences`
  (`email_alerts` key).

With no receipts uploaded yet the page shows an empty state: *"At least 2
matching transactions are needed to detect a subscription."*
