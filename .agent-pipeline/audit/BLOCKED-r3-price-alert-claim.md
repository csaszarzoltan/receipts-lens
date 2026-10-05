# RESOLVED (was: BLOCKED): F2.5 price-alert claim-before-send (R3 sign-off pending)

Date filed: 2026-10-02T05:40:18.863108
Resolved:   2026-10-05

Status: fix COMMITTED and pushed. The R3 human approval was granted and recorded.
This file is kept for the record, not as an open block.

- fix:   77741a8  fix(alerts): claim the price alert before sending, and release it on failure
- test:  f74abf9  test(alerts): prove the price-alert claim is taken before the send and released after
- gate:  scripts/veritas_gate.py approval recorded in .agent-pipeline/audit/veritas_audit.jsonl
         (`git show 2741628:...veritas_audit.jsonl | grep -c APPROVAL` -> 1)

The operational caveat below NO LONGER APPLIES: the claim is taken before the send, so two concurrent
`subscription-alerts` runs cannot both send. Leaving it stated as a live hazard was a defect in its own
right - the next agent would have re-fixed shipped code.

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

## How to unblock (historical — the block is lifted)
The gate (scripts/veritas_gate.py:190-196) accepts a non-empty
`VERITAS_APPROVAL` or `VERITAS_HUMAN_APPROVAL` env var. It is a bare
string check with no signature and no actor identity, so it must be set
by the human, in their own words:

    VERITAS_APPROVAL="<your own sign-off sentence>" git commit -a

Do NOT partial-commit: `app/product_service.py` alone ships dead code
(claim methods with no caller).

## Operational caveat — NO LONGER IN FORCE (was true before 77741a8)

Before the fix, two concurrent `subscription-alerts` runs could each send the same alert.
That is no longer the case: `subscription_alerts.py:948` now claims the send *before* the SMTP
call, so the second run sees the claim and skips. **This paragraph is kept only as history; it
is not an operational instruction.** The current rule is a different one and it is a real limit:

- **Duplicate-safe, not exactly-once.** The claim is a pre-send marker, not a lock around the
  send. A process killed between the claim INSERT and the SMTP call leaves the row claimed and
  that household's alert unsent; nothing reaps it (no TTL, no expiry-on-conflict — deferred to
  a spec of its own, `app/product_service.py:378`). So the guarantee bought by 77741a8 is
  "no silent double-mail on the graceful path", not "every alert arrives exactly once".
- **What this replaced:** the pre-fix text read "Two concurrent `subscription-alerts` runs WILL
  double-mail. Run it once at a time." That was the reason for the single-run constraint; the
  constraint is no longer the mitigation.
