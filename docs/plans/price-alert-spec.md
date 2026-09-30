# F2.5 — Price-increase email (un-orphan the shipped branch)

**Date:** 2026-09-29 | **Status:** ready for builder

**no-live-validation:** the on-disk brief (`.agent-pipeline/analysis/research-brief.md`, 2026-09-27) covers **F2.2 savings-summary**, not F2.5 — no primary snippet for this feature. Every fact below was re-verified in the working tree on 2026-09-29 and carries a `file:line`.

## Target files (allowlist — 4, nothing else)

`app/product_service.py` (+1 table, +2 methods) · `app/subscription_alerts.py` (shared builder, idempotency gate) · `app/subscriptions_api.py:106` (delegate) · `app/cli.py:15` (the caller). Tests are the tester's; this spec writes none.

## Verified baseline

`detect_price_increase` :159, `current > avg*1.10`, empty baseline→False — **threshold unchanged**. Price branch :707-727, counts only under `if sent:` (:722-723); returns :729-733. `send_email_notification` reads `to_addr` :499 and has **two silent-False gates**: host must match `[.:]` (:508-512), and `RECEIPTLENS_SMTP_ENABLED` (:515-518). **Zero production callers** of `daily_scheduler` (grep: definition + tests only). `app/recurring.py` references neither symbol — stays inert. No Alembic, no `alembic.ini`; schema is the inline `executescript` at `app/product_service.py:66-105`, `members` at :76-78. `list_members(actor)` :249-254 filters on `actor.tenant_id` only, no role check. `Actor` = bare dataclass `tenant_id, role` (:27); `HOUSEHOLD_ROLES` :34 has `owner`.

## Decision A — one truth, builder moves DOWN

Verified direction: `app/subscriptions_api.py:36` does a **module-level** `from app.subscription_alerts import (...)` and `app/product_api.py:562` builds `accounting`. So importing upward is a cycle — the code already defers it with a function-local import at :587.

1. Add `build_subscriptions(tenant)` to `app/subscription_alerts.py`: the body of `_build_subscriptions` verbatim **plus** the scheduler's `baseline` and `email_alert_enabled: True` keys; reach `accounting.recurring(tenant)` via the function-local import style at :587. No new module-level import → no cycle.
2. `_build_subscriptions` (subscriptions_api:106) becomes a projection dropping `baseline`/`email_alert_enabled`; the HTTP key set stays **byte-identical** — `baseline` must not leak into `GET /api/v1/subscriptions`.
3. `daily_scheduler` (:624) calls `build_subscriptions` in its own module — no import. Delete `_build_scheduler_subscriptions` (:579).
4. Divergence fixed: the old scheduler did `continue` on empty `last_date`; the API builder falls back to `_month_start_iso()`. Keep the **API** behaviour — a missing date must not silently drop a price alert.
5. DEMO stays scheduler-local: `build_subscriptions(tenant) or DEMO_SUBSCRIPTIONS` (:612) so `tests/test_subscription_alerts.py:663` still exercises the hike path. DEMO is a fixture, not a truth source.

## Decision B — the recipient crosses a *service* boundary, not a DB one

`AccountingWorkspace.db = product_service._db` (`app/accounting_workspace.py:18`) — one `sqlite3.Connection`, so **same database**. But `list_members` is a `ProductService` method taking an `Actor`, while `daily_scheduler` takes a bare `tenant: str`. Since it reads only `actor.tenant_id` and checks no role, the trigger synthesizes a read-only `Actor` (function-local `from app.product_api import service`; `"admin"` matches the legacy default in `subscriptions_api._actor`):

```python
owner = next((m["email"] for m in service.list_members(Actor(tenant, "admin"))
              if m["role"] == "owner" and m["active"]), None)
```

Then `smtp_config = {**smtp_config, "to_addr": owner}` — the **owner always wins** over a caller-supplied `to_addr`; warn when they differ. Guarded by `try/except ImportError` so the pure-alerts unit tests still pass without a product DB. 0 owners → `to_addr=None`, warn, send nothing. >1 owner → first by `email` (`:251` is `ORDER BY email`, so deterministic) + warn.

## DDL — appended to the `executescript` at :66-105, after `members` (:76-78)

Name `price_alert_sent` is effectively permanent: no migration system exists to rename it.

```sql
CREATE TABLE IF NOT EXISTS price_alert_sent(
  alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL, merchant TEXT NOT NULL,
  amount_cents INTEGER NOT NULL, period_ym TEXT NOT NULL,
  notified_at TEXT NOT NULL,
  UNIQUE(tenant_id, merchant, amount_cents, period_ym));
```

Plus `ProductService.has_price_alert_sent(tenant_id, merchant, amount_cents, period_ym) -> bool` and `record_price_alert_sent(...) -> bool` (`False` on `sqlite3.IntegrityError`). The trigger must not touch `_db` privately.

## Idempotency key — `(tenant_id, merchant, amount_cents, period_ym)`

Merchant alone is wrong: a merchant can hike twice (9.99→10.99 in March, 10.99→12.99 in October) and merchant-only would suppress the second, real alert forever. `amount_cents = int(round(amount*100))` (integer, no float drift); `period_ym = (renewal_date or anchor_iso)[:7]` — the billing month carried by the sub view-model. NOTE: `last_date` is deliberately NOT used; AC-3 pins the key set and `last_date` is not in it, and `renewal_date` is the only date the scheduler receives (subscription_alerts.py:670). For a monthly subscription the renewal date sits one month after the charge, so the key month is offset by one; this does not weaken idempotency (identical input → identical key) and it is what re-arms the alert in a later month. Re-running the same merchant/price/month is suppressed; the same price returning later (19.99→15.99→19.99) re-arms. Either field alone fails one of those.

## Ordering — a `sent` row must never be a lie

`if has_price_alert_sent(...): price_alerts_suppressed += 1; continue` → `sent = send_email_notification(...)` → **only `if sent:`** write the row and increment `price_emails_sent`. On `False` (either silent gate) or exception: no row, `logger.warning`, nothing counted.

## The caller

No cron, no daemon, no loop in this repo. Add `subscription-alerts` to `_build_parser()` (`app/cli.py`, next to `info` ~:95) and a dispatch arm in `main` (:15, next to `forecast` :37). `_cmd_price_alerts` builds `smtp_config` from `RECEIPTLENS_SMTP_HOST/PORT/USER/PASSWORD/FROM_ADDR` (`to_addr` comes from the trigger, Decision B), calls `daily_scheduler(smtp_config=..., tenant=args.tenant)`, returns `0` / `1` partial / `2` fatal per the contract at :15-19. `--dry-run` skips the write. **Scheduling it is the operator's job — out of scope.**

## Acceptance criteria

| AC | Assertion (literal) | Touches | RED first? |
|---|---|---|---|
| 1 | `has_price_alert_sent("demo","Netflix",1999,"2026-08")` `False` → after `record_price_alert_sent` `True`; a repeat call returns `False` and `SELECT COUNT(*) FROM price_alert_sent` is exactly `1` | product_service.py:76 + 2 methods | yes |
| 2 | Two `ProductService.__init__` against one file-backed DB → no error, table still 1 (no Alembic ⇒ `IF NOT EXISTS` must be idempotent) | product_service.py:66 | yes |
| 3 | `_build_subscriptions("demo")` key set is exactly `{id,merchant,occurrences,frequency,renewal_date,amount,monthly_cost,annualized,trend,price_increase,likely_subscription}`; assert `set(sub) == EXPECTED_KEYS` and `"baseline" not in sub` | subscriptions_api.py:106 | no (guard) |
| 4 | `from app.subscription_alerts import build_subscriptions` **and** `import app.subscriptions_api` succeed in one process — no `ImportError`, no cycle | both files | yes |
| 5 | A receipt with `last_date == ""` and ≥2 charges still appears in `build_subscriptions`, `price_increase` present, baseline = `amounts[-4:-1]` (old scheduler dropped it) | subscription_alerts.py:596 | yes |
| 6 | `daily_scheduler(subscriptions=[{"merchant":"Netflix","amount":19.99,"baseline":[15.99],"email_alert_enabled":True}], tenant="demo")` with a working `smtp_config` → `price_emails_sent == 1` and 1 row with `amount_cents == 1999` | subscription_alerts.py:707-727 | yes |
| 7 | Same input with `RECEIPTLENS_SMTP_ENABLED` unset (gate :515-518) → `price_emails_sent == 0` **and `COUNT(*) == 0`**; repeat with `host="localhost"` (gate :508-512) → same. The table must not lie | subscription_alerts.py:722 | yes |
| 8 | Run the AC-6 scenario twice → 2nd run `price_emails_sent == 0`, `price_alerts_suppressed == 1`, table still 1 row | idempotency gate | yes |
| 9 | Same merchant/amount/`period_ym="2026-08"` twice; then `period_ym="2026-11"` → `has_price_alert_sent` is `False` again (re-arms) | key definition | yes |
| 10 | 1 active owner `o@x.io` → sent `To:` is `o@x.io` **even though the caller passed `to_addr="other@x.io"`** | subscription_alerts.py:499 consumer, product_service.py:249 | yes |
| 11 | members `[(adult@x.io,adult,1),(o@x.io,owner,1),(old@x.io,owner,0)]` → recipient is exactly `o@x.io` (inactive owner and adult excluded) | product_service.py:249-254 | yes |
| 12 | No active owner → `price_emails_sent == 0`, `price_recipient is None`, `COUNT(*) == 0`, and `send_email_notification` never called (assert via a raising `smtp_config` sentinel) | Decision B | yes |
| 13 | `main(["subscription-alerts","--tenant","demo"])` → `0`; the subcommand appears in `main(["--help"])`; `--dry-run` writes nothing, exits `0` | cli.py:15,37,~95 | yes |
| 14 | Result dict gains exactly two keys, `price_alerts_suppressed` (an alert an EARLIER run already delivered — a success) and `price_alerts_failed` (a hike detected on THIS run that reached nobody — the only failure); `subscriptions_checked`/`renewal_emails_sent`/`price_emails_sent`/`date` unchanged and `renewal_emails_sent` identical before vs after the refactor | subscription_alerts.py:729-733 | no (guard) |
| 15 | `TEST-US023-021` (`tests/test_us_023_consumer_dashboard_contract.py:601`) still passes — `consumer_dashboard._price_alerts` unaffected | consumer_dashboard.py | no (guard) |
| 16 | `daily_scheduler` now appears in ≥2 files under `app/` (definition + `cli.py`); `app/recurring.py` gains no import of it | cli.py, recurring.py | yes |

**Anti-brittleness:** AC-7/AC-12 assert on **row counts and counter values**, never string distance. The implementer places marker comments `# AC-PRICE-7 gate` / `# AC-PRICE-12 gate` on the `if sent:` line and the recipient-lookup line so review can cite `file:line`.

## Out of scope

Renewal emails (the :676-705 branch keeps its unconditional behaviour) · `app/recurring.py` (dashboard statistic only, must never notify) · household invites / magic links · any opt-in or email-verification UI · cron or any real schedule · SMTP retry/backoff · bounce handling · per-merchant alert preferences · multi-recipient sends.

## Risks and accepted limitations

- **Single-instance assumption (accepted).** The scheduler assumes ONE instance runs at a time. The `price_alert_sent` UNIQUE key makes the bookkeeping safe — a second INSERT is a no-op — but it cannot make the SMTP send atomic, so two overlapping runs can each mail the household while the table correctly holds one row. `price_emails_sent` is deliberately not decremented (the mail really went out) and a duplicate send is not counted as a failed alert. Fixing it properly needs a transaction spanning the SMTP call, which we do not hold open. **This is now an operator-facing constraint, documented in `docs/subscription-alerts.md` ("Run one instance at a time") rather than living only in the `KNOWN LIMITATION` comment at `app/subscription_alerts.py:925`** — a second cron entry would duplicate a household's alert mail.
- **`members` has no opt-in and no email-verification column** (:76-78): any active owner address receives a price alert whether or not it asked to. Owner-only caps the blast radius at one address per household and stops one member's data leaking to another, but it does **not** make the send consented. Flagged during planning and still true. A `price_alerts_opt_in`/`verified_at` column plus an owner consent screen is the real fix — deferred, not forgotten.
- Two `role='owner'` rows in one tenant: the first-by-email pick is deterministic but may not be the intended recipient — a data-quality error, not a coin flip.
- `period_ym` is derived from `renewal_date`, so for a monthly subscription the key month is offset by one from the charge month. Accepted (see *Idempotency key*): identical input still yields an identical key, so idempotency is not weakened, and the offset is what re-arms the alert in a later month.
- `to_addr` is read from the merged config (:499); if the owner injection ever fails the mail goes to `None` or a stale address. AC-10/AC-12 pin this.
- `app/product_api.py:34` instantiates `ProductService` at import time from `RECEIPTLENS_PRODUCT_DB` (default `:memory:`), so AC-10/11 must seed through that same `service` singleton the trigger reads.
- The loader refactor touches the consumer dashboard's price alerts; AC-15 exists solely to catch a regression there.

**Handoff:** builder implements the 4 target files against AC-1..16; tester writes the RED suite first and reports the AC table.
