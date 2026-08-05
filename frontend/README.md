# ReceiptLens Frontend

Modern, product-ready **Next.js 14 (App Router) + React 18 + TypeScript + Tailwind CSS** frontend
for the ReceiptLens receipt-scanning and expense-tracking API. Replaces the legacy vanilla-JS
workspace UI.

## Stack

- **Next.js 14.2** App Router, React 18, TypeScript (strict mode)
- **Tailwind CSS 3.4** with design tokens (`tailwind.config.ts`), dark mode via `class` strategy
- **SWR** for server-state caching / revalidation of every API call
- **Recharts** for spending, forecast and budget-variance charts
- English-first **i18n** (`lib/i18n.ts`) with a `useTranslation()` hook and a Hungarian catalog

## Getting started

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # production build
npm run typecheck    # tsc --noEmit
```

The API client defaults to `http://localhost:8000` (FastAPI dev server). Override with:

```bash
NEXT_PUBLIC_API_BASE_URL=http://my-host:8000 npm run dev
```

The backend already enables CORS for all origins, so no proxy config is needed.

## Structure

```
app/
  layout.tsx              # Root layout (metadata, manifest)
  page.tsx                # Public landing page
  (app)/                  # Authenticated shell (Sidebar + MobileNav + Topbar)
    layout.tsx            # AppShell wrapper + Onboarding modal
    dashboard/            # KPI cards, spending trend, work queue
    receipts/             # Search + filters + pagination + table
    receipts/[id]/        # OCR result, image, line-item editor, history, validation
    upload/               # DropZone + camera capture + OCR preview queue
    review/  approvals/  duplicates/  automations/  accounting/
    exports/ (+prepare)  inbox/  subscriptions/  forecast/  budget/
    reports/  integrations/  settings/ (+profile, members, permissions, privacy, diagnostics)
  (auth)/login  (auth)/register
  onboarding/             # Standalone first-time setup flow
  manifest.ts             # PWA manifest
components/               # AppShell, Sidebar, MobileNav, Topbar, EmptyState,
                          # ConfidenceBadge, StatusBadge, Money, Pagination, FilterBar,
                          # Toast, Modal, Onboarding, DropZone, UploadQueue, Charts, …
lib/
  api.ts                  # Typed client for ALL backend endpoints (no mocks)
  types.ts                # 36+ TypeScript interfaces mirroring the API schemas
  auth.ts                 # X-Tenant-ID / X-Role header auth (localStorage-persisted)
  i18n.ts                 # en/hu catalogs + useTranslation
  utils.ts                # money/date/percent formatting helpers
  hooks/                  # SWR hooks (useReceipts, useDashboard, useForecast, useUpload)
```

## Data flow

Every page fetches real data through `lib/api.ts` — a fully typed client covering the
`/product/*`, `/forecasts/*` and `/api/v1/*` endpoint families (60+ functions). There is
**no mock data** anywhere in the client. Uploads use an XHR-based `uploadWithProgress()`
so the UI renders real per-file progress, then the OCR result preview.

## Responsive design

Mobile-first with Tailwind breakpoints (`sm` 480 / `md` 768 / `lg` 1024 / `xl` 1280):

- `<lg` — sidebar hidden, bottom tab bar (5 items) + hamburger slide-over menu
- `≥lg` — fixed 250px sidebar, sticky top bar with global search
- KPI grids: 2 cols on phones → 4 cols on desktop; every interactive target ≥ 44px

## Verification

```bash
cd .. && .venv/bin/python -m pytest tests/test_frontend.py   # 190 pre-written tests
cd frontend && npx tsc --noEmit                              # strict typecheck
npx next build                                               # production build
bash ~/.hermes/scripts/ui-gate.sh ..                          # modern-frontend gate
```
