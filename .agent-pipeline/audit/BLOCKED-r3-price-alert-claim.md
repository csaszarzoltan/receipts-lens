# BLOCKED: F2.5 price-alert claim-before-send (R3 sign-off pending)

Date: 2026-10-02T05:40:18.863108
Status: verified fix, NOT committed — VERITAS R3 gate requires human
approval because `app/subscription_alerts.py` is a sensitive path.

## What the bug was
`daily_scheduler` read `has_price_alert_sent` (False), sent the SMTP
mail, and only then wrote `price_alert_sent`. Two concurrent runs both
cleared the read, so the household received the same price-hike email
twice. The UNIQUE constraint deduped the bookkeeping but could not
un-send mail. The code documented this as a KNOWN LIMITATION.

## The fix
The ledger row becomes the mutual-exclusion token, acquired BEFORE the
send: `ProductService.claim_price_alert_sent` inserts first; the loser
gets IntegrityError -> False, suppresses, never sends. Every
non-delivery path calls `release_price_alert_sent` so a retry stays
possible. `busy_timeout` PRAGMA added; OperationalError re-raised so a
locked DB can never look like a won claim.

## Evidence
- RED before the fix: `assert 2 == 1`, "the household was mailed 2 times"
- GREEN after: 4 release + 2 concurrency + 9 F2.5 + 4 delivery-proof = 19 pass
- full suite: 1698 passed, 0 failed, 10 skipped
- ruff clean on both changed app files
- independent reviewer: APPROVE 4.0/5
- live ./receiptlens-product.db untouched throughout (price_alert_sent = 0)
- the release tests exposed three `pass  # MUTANT:` lines left in
  production code by a mutation run; all restored, `grep -c MUTANT` = 0

## How to unblock
The gate (scripts/veritas_gate.py:190-196) accepts a non-empty
`VERITAS_APPROVAL` or `VERITAS_HUMAN_APPROVAL` env var. It is a bare
string check with no signature and no actor identity, so it must be set
by the human, in their own words:

    VERITAS_APPROVAL="<your own sign-off sentence>" git commit -a

Do NOT partial-commit: `app/product_service.py` alone ships dead code
(claim methods with no caller).

## Operational caveat until committed
Two concurrent `subscription-alerts` runs WILL double-mail. Run it once
at a time; do not add a second cron entry or an overlapping manual run.
