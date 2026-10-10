# SPEC-050: OCR amounts, currency provenance and totals (retroactive)

**Status:** SHIPPED_RETROACTIVE — describes behaviour already implemented on
branch `fix/ocr-webhook-currency`; no production behaviour is introduced by this spec.
**Feature:** FEAT-050 · **Brief:** none (same pattern as SPEC-049) · **Risk:** high (money values)

## Problem

Receipt amounts were read silently wrong in several cases: whole-unit totals
(`TOTAL 1,234` → 1.23), space-grouped amounts, Hungarian total labels, dates
without a "Date:" label, currency defaults, and mixed-currency dashboard sums.
The OCR total was also hidden entirely when the merchant could not be read.

## Requirements and acceptance scenarios

| REQ | AC | Requirement (what must hold) | Verified by |
| :--- | :--- | :--- | :--- |
| FEAT-RL-V02-REQ-058 | AC-RL-V02-39 | Amounts are parsed with thousands and space grouping, cents-aware: a space is a quantity separator on receipts that print cents, a thousands separator otherwise; currency affixes on line items are accepted; discount lines keep their sign. | `tests/test_ocr_thousands.py`, `tests/test_ocr_coverage.py` |
| FEAT-RL-V02-REQ-059 | AC-RL-V02-40 | Hungarian receipts: `Összesen`/`Végösszeg`/`Fizetendő` (with and without accents) are totals; `Ft` after an amount means HUF; dates without a label are found and normalised to ISO; a requested `hun` OCR pack falls back to `eng` when not installed. | `tests/test_ocr_hu_receipt.py`, `tests/test_ocr_dates.py`, `tests/test_ocr_hu_language.py` |
| FEAT-RL-V02-REQ-060 | AC-RL-V02-41 | Missing currency is inferred from the same merchant's explicit receipts, then the tenant's, and always labelled (`currency_source`, `currency_assumed`); cents receipts are never inferred as a zero-decimal currency; a user-entered currency must be an ISO 4217 code and replaces the assumption. | `tests/test_currency_inference.py` |
| FEAT-RL-V02-REQ-061 | AC-RL-V02-42 | Dashboard totals are per currency: the budget currency (or largest spend) is reported, other currencies are listed separately and never summed or converted. | `tests/test_dashboard_currency.py` |
| FEAT-RL-V02-REQ-062 | AC-RL-V02-43 | A total withheld by the BUG-001 confidence gate is kept as `total_candidate` for user confirmation; it is saved as `total` only when the user confirms. | `tests/test_total_candidate.py` |
| FEAT-RL-V02-REQ-063 | AC-RL-V02-44 | Webhook delivery never reaches internal addresses: every resolved address is validated and the request connects to the validated IP (no second DNS lookup). | `tests/test_webhook_ssrf.py` |
| FEAT-RL-V02-REQ-064 | AC-RL-V02-45 | Low-DPI input is flagged low confidence with the Hungarian warning kept in the `hu` catalog; the total is withheld. | `tests/test_c3_pilot_red.py` |
| FEAT-RL-V02-REQ-065 | AC-RL-V02-46 | Loading skeletons exist for `/upload` and `/receipts`, and the C2 change touches no C3 file. | `tests/test_c2_skeletons_red.py` |

## Out of scope

- Currency conversion with exchange rates (planned separately: ECB daily reference rate).
- Household per-member attribution (planned separately: uploader is the owner).
- Automatic language detection for OCR (latency trade-off not decided).

## Evidence

Test ids `TEST-RL-V02-061` … `TEST-RL-V02-202` (142 functions) carry the markers above.
Full suite on the branch: see the commit that adds this spec.
