# QuickBooks Online sandbox connector

ReceiptLens now contains the provider-domain foundation for a tenant-scoped QuickBooks Online sandbox connection: single-use OAuth state, AES-GCM credential storage, immutable mapping versions, replay-safe item exports, provider links, reconciliation comparison, and source-currency/tax projections.

## Configuration

Set `RECEIPTLENS_CREDENTIAL_KEY` to a URL-safe Base64 encoding of exactly 32 random bytes. Keep the Intuit client identifier and secret outside the project tree. Sandbox is the only supported environment in this pass. Never store credentials in `.env` inside the repository.

## Workflow

1. Open **Integrations** and review requested scopes.
2. Connect the sandbox company through an OAuth callback handled by the connection service.
3. Validate and save an expense-account/tax mapping. Each save creates an immutable version.
4. Refresh receipt accounting projection when source and reporting currencies differ.
5. Create a provider run. Every item receives a deterministic dedupe key and a durable status.
6. Retry only failed items whose source version is unchanged.
7. Verify the remote purchase. ReceiptLens reports `verified`, `needs_reconciliation`, or `missing_remote`.

## Safety properties

Tokens are authenticated ciphertext, OAuth state is tenant-bound and single-use, provider hosts are fixed in the connector, successful links prevent duplicate creates, and provider errors are redacted. The implementation does not provide tax advice, production Intuit certification, Xero support, or automatic FX-rate retrieval.
