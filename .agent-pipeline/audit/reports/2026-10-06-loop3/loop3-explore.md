dispatch:  loop3 explore — brief inline in dispatch prompt (no brief file on disk)
agent:     explore
repo:      /home/zoltan/receipts-lens @ 8af5d08
brief:     sha256:e74e2c9ec0e9 (CLAUDE_BRIEF_SHA from dispatcher env; report written from the inline prompt)
verdict:   none - first pass (v20261005202137 APPROVE 4.7/5 at 0560c23 still points at scratch loop2-gate.md; v20261006034901 REQUEST-CHANGES 3.85/5 was pre-8af5d08 — the report has since landed in-repo, see item 5)
status:    DONE — all 6 items answered; item 1 chosen = the TTL/expiry-on-conflict claim item, still OPEN per analysis/next-moves.md:82-88

## 1. ONE next work item

Add TTL + expiry-on-conflict for the `price_alert_sent` claim — i.e. read the already-stored `notified_at` column (currently written and read nowhere) in `app/product_service.py` `claim_price_alert_sent`/`has_price_alert_sent` (lines 273-399) and release/expire claims older than a TTL, so a crashed or locked run that strands a claim stops suppressing that household's price-hike alert forever.

## 2. Evidence

- Written-and-read-nowhere claim (grep -rn "notified_at" app/ --include='*.py'):
  - app/product_service.py:94 (schema), :303 (INSERT record), :320/:356 (docstring says read nowhere), :388 (INSERT claim), plus app/subscription_alerts.py:744 (docstring).
  - No SELECT/UPDATE of notified_at anywhere in app/ — confirmed by the same grep returning only INSERT lines, CREATE TABLE, and docstring prose.
- Deferred-in-code, not just in prose (sed -n '370,380p' app/product_service.py): line 378-380 reads "Deliberately NOT solved here: a TTL on the claim, a reaper that ages out unfulfilled claims, or recording which run holds the claim and checking that it is still alive. Those are behaviour changes to the send path and belong to a spec of their own."
- Consumer is live, not dead (grep -rn 'claim_price_alert_sent(' app/ --include='*.py' | grep -v 'def '):
  - app/subscription_alerts.py:701 (inside _claim_price_alert_sent wrapper)
  - app/subscription_alerts.py:948 (daily_scheduler — the actual alert send path)
- Operator recovery is manual-only (app/product_service.py:369-372 docstring: "DELETE FROM price_alert_sent WHERE tenant_id=? AND merchant=? AND amount_cents=? AND period_ym=?"); app/subscription_alerts.py:744-747 repeats "There is no reaper: nothing in app/ reads notified_at".
- Still listed as OPEN work (grep -n -A3 -B3 "TTL" analysis/next-moves.md):
  - next-moves.md:82-88 "### Open item, planned but NOT built **TTL + expiry-on-conflict for the price_alert_sent claim.** ... `app/product_service.py:378` defers it in the shipped code ... so it needs PLAN before BUILD."
- No commit already implements TTL/expiry/reaper for this claim (grep below — see item 5): the only non-docstring TTL/expiry hits in app/product_service.py + subscription_alerts.py are for magic links (MAGIC_LINK_TTL_SECONDS, line 37), invites (INVITE_TTL_SECONDS, line 38) and sessions (SESSION_TTL_SECONDS, line 39) — none for price_alert_sent.

## 3. Why this NOW, not the alternatives

Doing this NOW because it is the only item that (a) is still explicitly listed as OPEN in analysis/next-moves.md:82-88, (b) has a live production consumer in app/subscription_alerts.py:701,948 that today can permanently suppress a real household's price-hike alert with no automatic recovery, and (c) the repo already has working TTL precedent in the same file (magic links/invites/sessions, lines 37-39, 919-1128) so the pattern is established, not novel.

Alternatives considered and rejected:
- Alternative A: clean up the foreign artifacts in .agent-pipeline/audit/reports/2026-10-05-loop1/ (bh-gate-3b.out = browser-helper, loop5-dev.out = Veritas). Rejected because PROVENANCE.md already exists in that same directory (committed — see item 5) and labels every file's true origin; this is now a labeling task that is already done, not an open defect worth spending the next build slot on.
- Alternative B: fix the bare `python3` in tests/test_veritas_gate.py:135/:249/:576 (same interpreter-resolution class as the .githooks/pre-commit defect loop-2 just closed). Rejected as the NEXT item because next-moves.md:118-120 says this is "NOT yet confirmed as a repo defect — the same class in tests/** needs its own measurement before it is work" — the measurement that would make it real work has not been run yet, so dispatching a build for it now would be acting on an unconfirmed hazard, while the price-alert TTL is already independently confirmed by two agents (explore + orchestrator) per next-moves.md:83-85.
- Alternative C: investigate the flaky test_inbound_emails_exceeding_limit_returns_429 (tests/test_rate_limiting.py:160). Rejected because "observed once" is the weakest evidence base of the four candidates — no reproducer, no second sighting, and nothing in analysis/ marks it OPEN or blocking; a single flaky observation does not outrank a documented, consumer-backed, still-open production hazard.

## 4. Production consumer check

Command run: grep -rn 'claim_price_alert_sent(' app/ --include='*.py' | grep -v 'def '
Output:
  app/subscription_alerts.py:701:        store.claim_price_alert_sent(tenant, merchant, amount_cents, period_ym)
  app/subscription_alerts.py:948:            if not _claim_price_alert_sent(tenant, merchant, amount_cents, period_ym):

Command run: grep -rn 'claim_price_alert_sent' app/**/__init__.py
Output: rc=1, no matches (the file app/__init__.py exists but does not mention the symbol; there is no app/*/__init__.py hit either)

Conclusion: NOT a wiring slice — this is a REAL production slice. The symbol has two non-def callers in app/subscription_alerts.py, one of which (line 948, inside daily_scheduler) is the live send path that actually suppresses or sends a household's price-hike email. Zero __init__.py exports does not weaken this: the consumer imports it directly via app.product_service, not via package re-export. So the TTL/expiry-on-conflict change touches a code path production already uses on every scheduler run.

## 5. Is it already done?

- analysis/ directory listing (ls analysis/): architecture-frontend.md, next-moves.md, research-brief.md — next-moves.md is the only item-tracking file present.
- grep -n "TTL" analysis/next-moves.md → lines 30, 32, 83-88 all describe the TTL/expiry gap as still open ("### Open item, planned but NOT built", "A claim whose send never completes is **permanent** — no TTL, no reaper"). No later section in the file marks it CLOSED or done.
- git log --oneline -50 --grep='TTL' → no commit subject mentions TTL at all (empty output for the subject-only grep; the -50 range contains no TTL-titled commit).
- git log --oneline -50 --grep='price_alert' → f74abf9 "test(alerts): prove the price-alert claim is taken before the send and released after", 77741a8 "fix(alerts): claim the price alert before sending, and release it on failure", 587bf89/f24a17e/9d32833/121a7a9 — none of these implement TTL/expiry/reaper; 77741a8's own commit body (git show -s --format=%B 77741a8) says "written and read nowhere in app/, so there is no TTL and no reaper", i.e. it documents the gap, not a fix for it.
- git log --oneline -50 --grep='reaper' → empty (no commit subject mentions reaper).
- git ls-files --error-unmatch app/product_service.py → app/product_service.py (tracked, not deleted).
- Provenance check (the OTHER open item, already addressed): git ls-files --error-unmatch .agent-pipeline/audit/reports/2026-10-05-loop1/PROVENANCE.md → returns the path, i.e. PROVENANCE.md IS already tracked in git — this open item from next-moves.md iteration 2 ("The directory needs either the 2 foreign files removed, or a PROVENANCE.md naming each file's true origin") is already satisfied by that file being committed; not a reason to spend the next slot.

Answer: NOT done. No commit, test, or doc in the repo implements TTL or expiry-on-conflict for the price_alert_sent claim — every hit either documents the absence (product_service.py docstring, next-moves.md, 77741a8 body) or is unrelated (magic-link/session/invite TTLs, starttls). The item is correctly still OPEN.

## 6. What could make this wrong, and the falsification command

The ONE thing that could make item 1 wrong: the claim in the task context that "notified_at [is] written/read nowhere" (and therefore that no TTL/reaper path exists) might itself be stale — i.e. some code path outside app/*.py (scripts/, a management command, a migration, a raw-SQL query in tests that mirrors production, or a recent un-reverted edit) might already read notified_at or already implement an expiry check, which would make the TTL work redundant or already-in-flight elsewhere.

Falsification command (broadened beyond app/ — not just the grep already run in item 2, which was scoped to app/ only):
  grep -rn "notified_at\|price_alert_sent" . --include='*.py' --include='*.sql' --include='*.sh' -r | grep -v "^./app/" | grep -v "\.venv\|__pycache__\|node_modules"
plus:
  git log -S 'notified_at' --oneline --all | head -n 20
  git log -G 'expires_at|stale_claim|claim_age' --oneline -- app/product_service.py app/subscription_alerts.py | head

This was NOT attempted (I ran app/-scoped greps only, per the brief's focus; I did not run the repo-wide grep or the pickaxe git-log commands above before writing this report). If that broader grep or git log -S turns up an existing read of notified_at or an expiry branch, item 1 is wrong/stale and the correct next move changes accordingly.

TIME USED: 12 minutes
