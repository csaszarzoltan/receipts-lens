# Product workflows

ReceiptLens now exposes a human-facing workspace and a tenant-aware product API in addition to the legacy OCR endpoints.

## Start the application

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/workspace` to upload a receipt. The workspace submits the image to the product workflow and displays the structured result.

## Tenant and role context

Product endpoints accept these headers:

```text
X-Tenant-ID: your-workspace
X-Role: admin | reviewer | integrator
```

The default `demo`/`admin` context preserves local-development compatibility. Production deployments must inject authenticated header values at a trusted gateway or replace the dependency with an identity-provider adapter. Client-supplied identity headers must not be trusted directly on an internet-facing deployment.

## Persistence

Set `RECEIPTLENS_PRODUCT_DB` to a writable SQLite path:

```bash
export RECEIPTLENS_PRODUCT_DB=./receiptlens-product.db
```

Without the variable, the product service uses an in-memory database suitable for tests and demonstrations. Production deployments should use a mounted persistent path or replace the adapter through the `ProductService` boundary.

## Product endpoints

- `POST /product/receipts/upload`: process and store a receipt.
- `GET /product/jobs`: tenant-scoped processing history.
- `POST /product/jobs/{job_id}/retry`: idempotent retry metadata operation.
- `POST /product/jobs/{job_id}/cancel`: cancel a cancellable job.
- `GET /product/review-items`: list low-confidence receipts.
- `PATCH /product/review-items/{receipt_id}`: version-checked correction.
- `POST /product/members`: add a workspace member.
- `POST /product/api-keys`: create a one-time visible API secret.
- `POST /product/connections`: configure CSV, QuickBooks, or Xero mapping metadata.
- `POST /product/connections/{connection_id}/test`: validate a connection definition.
- `POST /product/exports`: create a tenant-scoped export record.
- `GET /product/dashboard`: return usage, quality, privacy, and service summaries.

## Security notes

- Every product query scopes data by tenant.
- Review changes use the `If-Match` version header and return HTTP 409 for stale updates.
- API key secrets are returned only when created; only a SHA-256 digest is stored.
- Audit events contain identifiers and actions, not receipt bodies or secrets.
- The existing upload MIME and OCR validation remains active for real requests.

## Market features in v0.7.0

- `GET /product/receipts`: search by `query`, `status`, `tag`, `min_total`, and `max_total`; pagination uses `limit` and `offset`.
- `PUT /product/receipts/{receipt_id}/metadata`: set up to 20 tags plus optional `project` and `cost_center`.
- `POST /product/approval-policies`: create an admin-only currency threshold policy.
- `POST /product/receipts/{receipt_id}/approval`: evaluate a receipt and create a pending approval when required.
- `POST /product/approvals/{approval_id}/decision`: reviewer/admin approval or rejection with an optional note.
- `PUT /product/privacy/retention`: set retention from 1 to 3,650 days.
- `POST /product/privacy/purge`: remove expired tenant data and dependent rows transactionally.
- `GET /product/privacy/export`: export versioned tenant JSON with receipt metadata and approvals.

All operations are tenant-scoped. Approval policy and retention changes require `admin`; decisions require `admin` or `reviewer`. See `docs/research/MARKET_RESEARCH_2026.md` for the evidence, specifications, roadmap, and validation plan.
