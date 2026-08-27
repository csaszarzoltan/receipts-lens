# SPEC-ADR-004: Tax Pro Pack

## Target Files
- `app/taxonomy.py` (NEW)
- `app/tax_service.py` (NEW)
- `app/tax_audit.py` (NEW)
- `app/tax_api.py` (NEW)

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
