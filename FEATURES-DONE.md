# Features Done

## Features Done (this pass)
- US-019 consumer pivot F1.1: household navigation (Vásárlások, Nyugta hozzáadása, Ellenőrzés, Háztartási keret, Előfizetések, Előrejelzés, Összesítés, Családi postafiók, Ismétlődések) with zero business jargon in the main navigation.
- Business features (Approvals, Export Center, Accounting, Integrations, Automations) hidden behind a separate "Business" entry point — not deleted, still reachable.
- Household role naming: admin → Háztartás tulajdonosa, reviewer → Felnőtt tag, integrator → Könyvelő / tanácsadó (Business mód); target-state roles (Gyermek / korlátozott tag, Csak megtekintés) prepared for F1.3.
- Role surfaces (login, onboarding, topbar, members, permissions) display household labels; tenant wording replaced with Háztartás; tenant selector removed from the consumer topbar.
- Consumer page sweep: receipt detail drops cost-center input + export-readiness panel, Reports drops export activity, inbox becomes Családi postafiók, status badges use household labels. Wire format untouched.

## Sources
- docs/plans/consumer-pivot-2026-08-13.md §3.2 (role naming) and §3.3 (navigation).
- user stories covered: US-019 (consumer navigation & role naming).
- CHANGELOG.md section this maps to: `[Unreleased] - 2026-08-13 (US-019 consumer pivot F1.1)`.

## Previous pass
- Provider connection administration: tenant-scoped list/detail endpoints, admin-only disconnect that removes active credential ciphertext, and durable disconnected metadata.
- Versioned accounting mapping API: admin-only immutable mapping save and current-version retrieval with field validation.
- OAuth boundary hardening: open redirect rejection and tested fail-closed credential configuration.
