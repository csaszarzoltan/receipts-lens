# SPEC-ADR-006: QBO/Xero Sync and Accountant Invite

## Target Files
- `app/sync_service.py` (NEW)
- `app/sync_api.py` (NEW)
- `app/accountant_invite.py` (NEW)

## Typing & Signatures
All public services use explicit tenant identifiers and typed request/result objects.

## Step-by-Step Logic
1. Authenticate and resolve tenant.
2. Apply quota or Pro entitlement gate.
3. Validate enums, dates, and identifiers.
4. Execute tenant-scoped persistence atomically.
5. Return stable HTTP contracts; use 402 for paid-only operations.

## Unit Test Cases
- Table-driven rule matching.
- Tenant isolation.
- Boundary, rollover, expiry and content-type assertions.
