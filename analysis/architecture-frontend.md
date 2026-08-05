# ReceiptLens Frontend Architecture

## Overview

This document defines the React/Next.js TypeScript frontend architecture for ReceiptLens, replacing the current vanilla JS workspace (`workspace.js` / `workspace.html` / `workspace.css`). The design follows the patterns established in `/home/zoltan/mealmind` (Next.js 14 App Router, React 18, typed API client, service worker, i18n).

**Backend**: FastAPI v1.3.0 with 60+ REST endpoints across product, accounting, forecast, batch, and export domains.

---

## 1. Project Structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout: html lang, globals.css, ServiceWorkerRegister
│   ├── page.tsx                # Landing page / marketing
│   ├── globals.css             # Tailwind imports + custom design tokens
│   ├── (auth)/
│   │   ├── login/page.tsx      # Tenant/role selector (multi-tenant demo)
│   │   └── register/page.tsx   # Account creation (future)
│   ├── (app)/                  # Authenticated shell — wraps AppShell
│   │   ├── layout.tsx          # AppShell wrapper with sidebar nav
│   │   ├── dashboard/page.tsx  # KPI grid + next actions + spending chart
│   │   ├── receipts/
│   │   │   ├── page.tsx        # Receipt list with filters, saved views, bulk actions
│   │   │   └── [id]/page.tsx   # Receipt detail: metadata, history, validation, line items
│   │   ├── upload/page.tsx     # Drag-and-drop + camera + clipboard upload
│   │   ├── review/page.tsx     # OCR review workspace: side-by-side image + form
│   │   ├── approvals/page.tsx  # Approval queue with decision dialogs
│   │   ├── duplicates/page.tsx # Duplicate candidate comparison
│   │   ├── automations/page.tsx# Automation rules CRUD
│   │   ├── accounting/page.tsx # Accounting readiness: validation, line items, field links
│   │   ├── exports/
│   │   │   ├── page.tsx        # Export center: connections, export history
│   │   │   └── prepare/page.tsx# Export preparation & validation
│   │   ├── inbox/page.tsx      # Inbound email inbox
│   │   ├── subscriptions/page.tsx # Recurring expense detection
│   │   ├── forecast/page.tsx   # Forecast dashboard: projections, anomalies, budget variance
│   │   ├── reports/page.tsx    # Reports & analytics
│   │   ├── integrations/page.tsx # Connection management (CSV, QuickBooks, Xero)
│   │   └── settings/
│   │       ├── page.tsx        # Settings tabs container
│   │       ├── profile/page.tsx    # Preferences, language, accessibility
│   │       ├── members/page.tsx    # Team member management
│   │       ├── permissions/page.tsx# RBAC permission matrix
│   │       ├── privacy/page.tsx    # Retention, purge, export data
│   │       └── diagnostics/page.tsx# System diagnostics + bundle download
│   └── manifest.ts             # PWA manifest generator
├── components/
│   ├── AppShell.tsx            # Sidebar + topbar + mobile nav
│   ├── Sidebar.tsx             # Navigation sidebar (desktop)
│   ├── MobileNav.tsx           # Bottom tab bar (mobile)
│   ├── Topbar.tsx              # Search, tenant selector, notifications
│   ├── Toast.tsx               # Toast notification system
│   ├── Modal.tsx               # Reusable dialog/modal
│   ├── EmptyState.tsx          # Consistent empty state component
│   ├── ConfidenceBadge.tsx     # OCR confidence indicator
│   ├── StatusBadge.tsx         # Status/readiness badge
│   ├── Money.tsx               # Currency-aware amount display
│   ├── Pagination.tsx          # Reusable pagination controls
│   ├── FilterBar.tsx           # Reusable filter controls
│   ├── BulkActions.tsx         # Multi-select action bar
│   ├── UploadQueue.tsx         # File upload queue with progress
│   ├── DropZone.tsx            # Drag-and-drop + paste upload area
│   ├── ReviewWorkspace.tsx     # Side-by-side OCR review
│   ├── ApprovalCard.tsx        # Approval decision card
│   ├── DuplicateCard.tsx       # Duplicate comparison card
│   ├── RuleCard.tsx            # Automation rule card
│   ├── NotificationPanel.tsx   # Notification center
│   ├── Onboarding.tsx          # First-run onboarding flow
│   ├── PermissionMatrix.tsx    # RBAC permission editor
│   └── ServiceWorkerRegister.tsx # SW lifecycle
├── lib/
│   ├── api.ts                  # Typed API client (all endpoints)
│   ├── types.ts                # TypeScript interfaces for all data models
│   ├── i18n.ts                 # Internationalization (en-first, hu future)
│   ├── auth.ts                 # Tenant/role management (header-based)
│   ├── hooks/
│   │   ├── useReceipts.ts      # Receipt list SWR hook
│   │   ├── useDashboard.ts     # Dashboard data aggregation
│   │   ├── useReviews.ts       # Review items polling
│   │   ├── useApprovals.ts     # Approval list
│   │   ├── useNotifications.ts # Notification polling
│   │   ├── useForecast.ts      # Forecast data
│   │   ├── useUpload.ts        # Upload queue state machine
│   │   └── useOptimistic.ts    # Optimistic update helper
│   └── utils.ts                # Money formatting, HTML escaping, date helpers
├── public/
│   ├── icons/                  # PWA icons
│   └── manifest.webmanifest    # Static manifest (fallback)
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## 2. Component Hierarchy

### Root Layout (`app/layout.tsx`)
```
<html lang="en">
  <body>
    <ServiceWorkerRegister />
    {children}              # Pages render here
  </body>
</html>
```

### App Shell (`app/(app)/layout.tsx`)
```
<div className="app-shell">
  <a className="skip-link" href="#main">Skip to content</a>
  <Sidebar />              # Desktop: fixed left sidebar
  <MobileNav />            # Mobile: bottom tab bar
  <div className="main-column">
    <Topbar />             # Sticky top bar: search, tenant, notifications
    <main id="main" tabIndex={-1}>
      {children}           # Page content
    </main>
  </div>
  <NotificationPanel />    # Slide-over notification center
  <Toast />                # Global toast container
</div>
```

### Sidebar Navigation Items
```
Dashboard          → /dashboard
Receipts (count)   → /receipts
Upload             → /upload
Review (count)     → /review
Approvals (count)  → /approvals
Duplicates         → /duplicates
Automations        → /automations
Accounting         → /accounting
Export Center      → /exports
Email Inbox        → /inbox
Subscriptions      → /subscriptions
Forecast           → /forecast
Reports            → /reports
Integrations       → /integrations
Settings           → /settings
```

---

## 3. State Management

### Strategy: React Server Components + SWR for Server State

**Server Components (default)**: All pages that only read data are Server Components. They fetch data at request time and render HTML directly. This eliminates client-side waterfalls for read-heavy pages.

**Client Components (`"use client"`)**: Only components needing interactivity:
- `UploadQueue` (file state machine)
- `ReviewWorkspace` (form state, zoom/rotate)
- `ApprovalCard` (decision dialogs)
- `FilterBar` (local filter state)
- `BulkActions` (selection state)
- `PermissionMatrix` (checkbox state)
- `NotificationPanel` (polling)

**SWR for Server State**: All API calls use `swr` (or `@tanstack/react-query`) for:
- Automatic caching and revalidation
- Optimistic updates for mutations
- Background refetching on window focus
- Error retry with exponential backoff

**No Global State Store**: The app is inherently server-driven. Each page owns its data via SWR hooks. The only client-side shared state is:
- Tenant/role selection (stored in URL search params or localStorage)
- Upload queue (local component state)
- UI preferences (localStorage)

---

## 4. API Client Layer

### Design Pattern (from mealmind)

```typescript
// lib/api.ts
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// Generic typed request function
async function request<T>(path: string, options: RequestInit = {}): Promise<T>

// Tenant-aware request (attaches X-Tenant-ID, X-Role headers)
function tenantRequest<T>(path: string, options: RequestInit = {}): Promise<T>

// File upload with progress (XMLHttpRequest-based)
function uploadWithProgress<T>(path: string, file: File, onProgress?: (pct: number) => void): Promise<T>
```

### Headers
Every request includes:
```
X-Tenant-ID: <selected tenant>     # Default: "demo"
X-Role: <selected role>            # Default: "admin"
Content-Type: application/json     # (overridden for FormData)
```

### Error Handling
```typescript
export class ApiError extends Error {
  status: number;
  code?: string;
  retryable: boolean;
  retryAfterSeconds?: number;
}
```

---

## 5. Routing Map

| Route | Page Component | API Endpoints Used | Auth Required |
|-------|---------------|-------------------|---------------|
| `/dashboard` | DashboardPage | `GET /product/dashboard`, `GET /product/receipts?limit=200`, `GET /product/approvals`, `GET /product/work-queue?limit=8` | Yes |
| `/receipts` | ReceiptsPage | `GET /product/receipts`, `GET /product/saved-views` | Yes |
| `/receipts/[id]` | ReceiptDetailPage | `GET /product/receipts`, `GET /product/receipts/{id}/history`, `GET /product/receipts/{id}/validation`, `GET /product/receipts/{id}/ocr-boxes`, `GET /product/receipts/{id}/image` | Yes |
| `/upload` | UploadPage | `POST /product/receipts/upload` | Yes |
| `/review` | ReviewPage | `GET /product/review-items`, `PATCH /product/receipts/{id}/workspace`, `GET /product/receipts/{id}/image`, `GET /product/receipts/{id}/ocr-boxes` | Yes |
| `/approvals` | ApprovalsPage | `GET /product/approvals`, `POST /product/approvals/{id}/decision`, `POST /product/approval-policies` | Yes |
| `/duplicates` | DuplicatesPage | `GET /product/duplicates`, `POST /product/duplicates/decision` | Yes |
| `/automations` | AutomationsPage | `GET /product/automation-rules`, `POST /product/automation-rules`, `POST /product/automation-rules/preview` | Yes |
| `/accounting` | AccountingPage | `GET /product/receipts`, `GET /product/receipts/{id}/validation`, `GET /product/receipts/{id}/ocr-boxes`, `PUT /product/receipts/{id}/line-items` | Yes |
| `/exports` | ExportsPage | `GET /product/connections`, `POST /product/connections`, `POST /product/connections/{id}/test`, `GET /product/export-runs` | Yes |
| `/exports/prepare` | ExportPrepPage | `POST /product/export-preparations` | Yes |
| `/inbox` | InboxPage | `GET /product/inbound-emails`, `POST /product/inbound-emails` | Yes |
| `/subscriptions` | SubscriptionsPage | `GET /product/recurring-expenses`, `POST /product/recurring-expenses/feedback` | Yes |
| `/forecast` | ForecastPage | `GET /forecasts`, `GET /forecasts/anomalies`, `GET /forecasts/budget-variance` | Yes |
| `/reports` | ReportsPage | `GET /product/receipts`, `GET /product/export-runs` | Yes |
| `/integrations` | IntegrationsPage | `GET /product/connections`, `POST /product/connections`, `POST /product/connections/{id}/test` | Yes |
| `/settings/profile` | ProfileSettings | `GET /product/preferences`, `PUT /product/preferences` | Yes |
| `/settings/members` | MembersSettings | `GET /product/members`, `POST /product/members` | Yes |
| `/settings/permissions` | PermissionsSettings | `GET /product/permissions`, `PUT /product/permissions` | Yes |
| `/settings/privacy` | PrivacySettings | `GET /product/privacy/export`, `PUT /product/privacy/retention`, `POST /product/privacy/purge` | Yes |
| `/settings/diagnostics` | DiagnosticsSettings | `GET /product/diagnostics`, `GET /product/diagnostics/bundle` | Yes |
| `/login` | LoginPage | (none — tenant/role selector) | No |

---

## 6. Data Models / TypeScript Interfaces

```typescript
// lib/types.ts

// --- Core Receipt ---
export interface Receipt {
  vendor: string;
  total: number | null;
  date: string | null;
  tax: number | null;
  currency: string | null;
  line_items: LineItem[];
  confidence: Record<string, number>;
  category?: string;
}

export interface LineItem {
  name: string;
  price: number;
  quantity?: number;
  unit_price?: number;
  amount?: number;
  category?: string | null;
}

export interface ReceiptItem {
  receipt_id: string;
  receipt: Receipt;
  metadata: ReceiptMetadata | null;
  status: ReceiptStatus;
  version: number;
  readiness: ReadinessInfo;
  created_at: string;
}

export type ReceiptStatus =
  | "needs_review"
  | "completed"
  | "pending"
  | "approved"
  | "rejected"
  | "failed";

export interface ReceiptMetadata {
  tags: string[];
  project: string | null;
  cost_center: string | null;
}

export interface ReadinessInfo {
  state: "exportable" | "warning" | "blocked";
  issues: Array<{ message: string; severity: string }>;
}

// --- Dashboard ---
export interface DashboardData {
  service: { status: string };
  usage: {
    jobs_by_status: Record<string, number>;
    [key: string]: unknown;
  };
  quality: {
    needs_review: number;
    corrections: number;
  };
}

// --- Review ---
export interface ReviewItem {
  receipt_id: string;
  receipt: Receipt;
  version: number;
}

// --- Approvals ---
export interface Approval {
  approval_id: string;
  receipt_id: string;
  policy_id: string;
  policy_name?: string;
  status: "pending" | "approved" | "rejected";
  vendor?: string;
  total?: number;
  currency?: string;
  project?: string;
  note?: string | null;
  decided_by?: string | null;
  created_at: string;
  decided_at?: string | null;
}

export interface ApprovalPolicy {
  policy_id: string;
  name: string;
  threshold: number;
  currency: string;
  active: boolean;
  created_at: string;
}

// --- Duplicates ---
export interface DuplicateCandidate {
  left_id: string;
  right_id: string;
  left: Receipt;
  right: Receipt;
  confidence: number;
}

// --- Automation Rules ---
export interface AutomationRule {
  rule_id: string;
  name: string;
  conditions: Record<string, unknown>;
  actions: Record<string, unknown>;
  priority: number;
  active: boolean;
}

// --- Connections / Integrations ---
export interface Connection {
  connection_id: string;
  name: string;
  provider: "csv" | "quickbooks" | "xero";
  mapping: Record<string, string>;
  active: boolean;
}

// --- Export ---
export interface ExportRun {
  export_id: string;
  format: string;
  status: string;
  created_at: string;
}

export interface ExportPreparation {
  status: string;
  valid_ids: string[];
  blocked: Array<{ receipt_id: string; reason: string }>;
  warnings: Array<{ receipt_id: string; reason: string }>;
}

// --- Accounting ---
export interface ValidationResult {
  readiness: string;
  errors: Array<{ message: string }>;
  warnings: Array<{ message: string }>;
}

export interface OCRBox {
  text: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface HistoryEntry {
  action: string;
  created_at: string;
  actor_role: string;
  before?: Record<string, unknown> | null;
  after?: Record<string, unknown> | null;
}

// --- Forecast ---
export interface ForecastResult {
  period: string;
  currency: string;
  forecasts: ForecastEntry[];
  source_range: { date_from: string; date_to: string };
  narrative?: string;
}

export interface ForecastEntry {
  category: string;
  next_period_total: number;
  confidence_low: number;
  confidence_high: number;
  trend: number;
  method: string;
}

export interface AnomalyResult {
  method: string;
  threshold: number;
  anomalies: AnomalyEntry[];
}

export interface AnomalyEntry {
  period: string;
  category: string;
  expected: number;
  actual: number;
  score: number;
  flagged: boolean;
}

export interface BudgetVarianceResult {
  currency: string;
  projections: BudgetProjection[];
}

export interface BudgetProjection {
  budget_id: string;
  category: string;
  period: string;
  budgeted: number;
  projected_spend: number;
  expected_overage: number;
  status: "on_track" | "warning" | "over_budget";
}

// --- Work Queue ---
export interface WorkQueueItem {
  title: string;
  reason: string;
  action_url: string;
  action_label: string;
}

// --- Notifications ---
export interface Notification {
  notification_id: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

// --- Saved Views ---
export interface SavedView {
  view_id: string;
  name: string;
  filters: Record<string, unknown>;
  shared: boolean;
  pinned: boolean;
}

// --- Members ---
export interface Member {
  member_id: string;
  email: string;
  role: "admin" | "reviewer" | "integrator";
  active: boolean;
}

// --- Permissions ---
export interface PermissionMatrix {
  roles: Record<string, string[]>;
}

// --- Preferences ---
export interface Preferences {
  language: string;
  compact: boolean;
  high_contrast: boolean;
  onboarding_done: boolean;
  dashboard_widgets?: string[];
}

// --- Recurring Expenses ---
export interface RecurringExpense {
  merchant: string;
  annualized: number;
  occurrences: number;
  price_change: number;
  likely_subscription: boolean;
}

// --- Inbound Emails ---
export interface InboundEmail {
  sender: string;
  subject: string;
  attachments: Array<{ filename: string; content_type: string; size: number }>;
  status: string;
}

// --- Jobs ---
export interface Job {
  job_id: string;
  receipt_id: string;
  status: string;
  attempt: number;
  error: string | null;
  created_at: string;
}

// --- Batch ---
export interface BatchJob {
  job_id: string;
  status: string;
  total: number;
  completed: number;
}

// --- Export Formats ---
export interface ExportFormat {
  name: string;
  columns: string[];
  delimiter: string;
}

// --- Approval Flows ---
export interface ApprovalFlow {
  flow_id: string;
  name: string;
  definition: Record<string, unknown>;
}

// --- Diagnostics ---
export interface Diagnostics {
  version: string;
  database: string;
  receipt_count: number;
  failed_jobs: number;
  pwa: boolean;
  ocr: string;
}

// --- Exchange Rates ---
export interface ExchangeRate {
  base: string;
  quote: string;
  rate: number;
  rate_date: string;
  source: string;
}
```

---

## 7. Responsive Design Strategy

### Mobile-First with Tailwind CSS

**Breakpoints** (matching current CSS):
- `sm`: 480px (phone portrait)
- `md`: 760px (phone landscape / small tablet)
- `lg`: 1050px (tablet)
- `xl`: 1280px (desktop)

**Layout Behavior**:
- **Desktop (≥1050px)**: Fixed sidebar (250px) + scrollable main column
- **Tablet (760-1049px)**: Collapsible sidebar overlay + main content
- **Phone (<760px)**: Bottom tab bar (5 items) + hamburger menu for rest

**Component Patterns**:
- KPI grid: 4 cols desktop → 3 cols tablet → 2 cols phone
- Filter bar: horizontal row desktop → 2-col grid tablet → stacked phone
- Receipt table: horizontal scroll on phone (sticky first column)
- Review workspace: side-by-side desktop → stacked phone (image top, form bottom)
- Approval cards: 2-col grid desktop → single column phone

**Touch Targets**: Minimum 44x44px for all interactive elements on mobile.

---

## 8. Internationalization (i18n)

### Structure: English-First with Future Language Support

```typescript
// lib/i18n.ts
export type Locale = "en" | "hu";

export const messages = {
  en: {
    dashboard: "Dashboard",
    receipts: "Receipts",
    upload: "Upload",
    review: "Review",
    approvals: "Approvals",
    duplicates: "Duplicates",
    automations: "Automations",
    accounting: "Accounting",
    exports: "Export Center",
    inbox: "Email Inbox",
    subscriptions: "Subscriptions",
    forecast: "Forecast",
    reports: "Reports",
    integrations: "Integrations",
    settings: "Settings",
    // ... more keys
  },
  hu: {
    dashboard: "Áttekintés",
    receipts: "Nyugták",
    upload: "Feltöltés",
    review: "Ellenőrzés",
    approvals: "Jóváhagyások",
    duplicates: "Duplikátumok",
    automations: "Automatizálás",
    accounting: "Könyvelési ellenőrzés",
    exports: "Exportközpont",
    inbox: "E-mail inbox",
    subscriptions: "Előfizetések",
    forecast: "Előrejelzés",
    reports: "Riportok",
    integrations: "Integrációk",
    settings: "Beállítások",
    // ... more keys
  },
} as const;

export function t(key: keyof typeof messages.en, locale: Locale = "en"): string {
  return messages[locale]?.[key] ?? messages.en[key] ?? key;
}
```

**Currency Formatting**: Uses `Intl.NumberFormat` with locale-aware currency display. Default currency is configurable per tenant.

**Date Formatting**: Uses `Intl.DateTimeFormat` with locale. Dates are stored as ISO strings (YYYY-MM-DD) in the API.

---

## 9. Onboarding Flow Design

### First-Run Experience

When `preferences.onboarding_done === false`, display a modal overlay:

1. **Welcome**: "Welcome to ReceiptLens" — brief value proposition
2. **Upload First Receipt**: Guided upload with camera/file picker
3. **Review & Confirm**: Show OCR results, encourage review
4. **Dashboard Tour**: Highlight KPI cards and next actions
5. **Settings**: Quick language/currency selection

The onboarding modal:
- Has a "Skip" button that marks onboarding as done
- Each step has a "Next" / "Done" button
- Progress indicator at top (step 1 of 4)
- Can be re-triggered from Settings → Profile

---

## 10. Empty State Patterns

Every list/view page needs a consistent empty state:

```typescript
// components/EmptyState.tsx
interface EmptyStateProps {
  icon: string;        // Emoji or icon name
  title: string;       // Primary message
  description: string; // Secondary explanation
  action?: {
    label: string;
    href: string;
  };
}
```

**Page-Specific Empty States**:

| Page | Icon | Title | Description |
|------|------|-------|-------------|
| Receipts | 📄 | No receipts yet | Upload your first receipt to get started |
| Review | ✅ | All clear! | No receipts need review right now |
| Approvals | 🎯 | Nothing pending | All approvals are up to date |
| Duplicates | 🔄 | No duplicates found | Your receipt data looks clean |
| Automations | ⚡ | No rules yet | Create rules to automate categorization |
| Inbox | 📧 | No emails received | Forward receipts to your inbox address |
| Subscriptions | 🔄 | No recurring expenses | At least 2 matching transactions needed |
| Forecast | 📊 | Not enough data | Need at least 2 periods of history |

---

## 11. API Integration Spec

### Complete Endpoint Mapping

#### Health & Platform
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/health` | `getHealth()` | — | `{ status: "ok" }` |
| GET | `/ready` | `getReadiness()` | — | `{ status, dependencies }` |
| GET | `/api/v1/platform/capabilities` | `getCapabilities()` | — | `{ schema_version, requirements }` |

#### Receipt CRUD
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| POST | `/product/receipts/upload` | `uploadReceipt(file)` | FormData(file) | `ReceiptItem` |
| GET | `/product/receipts` | `searchReceipts(params)` | query: query, status, tag, min_total, max_total, limit, offset, readiness | `{ items: ReceiptItem[], total, offset, limit }` |
| GET | `/product/receipts/{id}/image` | `getReceiptImage(id)` | — | Blob (image) |
| GET | `/product/receipts/{id}/ocr-boxes` | `getReceiptBoxes(id)` | — | `{ receipt_id, boxes: OCRBox[] }` |
| GET | `/product/receipts/{id}/history` | `getReceiptHistory(id)` | — | `{ items: HistoryEntry[] }` |
| GET | `/product/receipts/{id}/validation` | `validateReceipt(id)` | query: connection_id? | `ValidationResult` |
| PUT | `/product/receipts/{id}/metadata` | `updateMetadata(id, body)` | `{ tags, project, cost_center }` | `ReceiptItem` |
| PATCH | `/product/receipts/{id}/workspace` | `updateReceiptWorkspace(id, body, version)` | `{ fields, line_items?, metadata?, action }` + If-Match header | `{ version }` |
| PUT | `/product/receipts/{id}/line-items` | `updateLineItems(id, items, version)` | `{ items, expected_version }` | `{ line_items, version }` |

#### Review Items
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/review-items` | `getReviewItems()` | — | `{ items: ReviewItem[] }` |
| PATCH | `/product/review-items/{id}` | `correctReceipt(id, body, version)` | `{ changes, action }` + If-Match | `ReviewItem` |

#### Approvals
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/approvals` | `getApprovals(status?)` | query: status? | `{ items: Approval[] }` |
| POST | `/product/approvals/{id}/decision` | `decideApproval(id, decision, note?)` | `{ decision, note? }` | `Approval` |
| POST | `/product/approval-policies` | `createApprovalPolicy(body)` | `{ name, threshold, currency }` | `ApprovalPolicy` |
| POST | `/product/receipts/{id}/approval` | `requestApproval(id)` | — | `Approval` |

#### Duplicates
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/duplicates` | `getDuplicates()` | — | `{ items: DuplicateCandidate[] }` |
| POST | `/product/duplicates/decision` | `decideDuplicate(leftId, rightId, decision)` | `{ left_id, right_id, decision }` | result |

#### Automation Rules
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/automation-rules` | `getRules()` | — | `{ items: AutomationRule[] }` |
| POST | `/product/automation-rules` | `createRule(body)` | `{ name, conditions, actions, priority }` | `AutomationRule` |
| POST | `/product/automation-rules/preview` | `previewRule(body)` | `{ conditions }` | `{ matching_receipts }` |

#### Saved Views
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/saved-views` | `getSavedViews()` | — | `{ items: SavedView[] }` |
| POST | `/product/saved-views` | `createSavedView(body)` | `{ name, filters, shared, pinned }` | `SavedView` |
| DELETE | `/product/saved-views/{id}` | `deleteSavedView(id)` | — | `{ status, view_id }` |

#### Notifications
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/notifications` | `getNotifications(includeArchived?)` | query: include_archived? | `{ items: Notification[], unread_count }` |
| PATCH | `/product/notifications/{id}` | `updateNotification(id, body)` | `{ read?, archived? }` | `Notification` |
| POST | `/product/notifications/read-all` | `markAllRead()` | — | `{ updated }` |

#### Members
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/members` | `getMembers()` | — | `{ items: Member[] }` |
| POST | `/product/members` | `addMember(body)` | `{ email, role }` | `Member` |

#### API Keys
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| POST | `/product/api-keys` | `createApiKey(body)` | `{ name }` | `{ key_id, name, secret }` |

#### Connections
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/connections` | `getConnections()` | — | `{ items: Connection[] }` |
| POST | `/product/connections` | `createConnection(body)` | `{ name, provider, mapping }` | `Connection` |
| POST | `/product/connections/{id}/test` | `testConnection(id)` | — | result |

#### Exports
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| POST | `/product/exports` | `createExport(body)` | `{ connection_id, receipt_ids }` | `ExportRun` |
| GET | `/product/export-runs` | `getExportRuns()` | — | `{ items: ExportRun[] }` |
| POST | `/product/export-preparations` | `prepareExport(body)` | `{ receipt_ids, connection_id? }` | `ExportPreparation` |
| GET | `/product/export-preparations` | `getExportPreparations()` | — | `{ items }` |
| GET | `/api/v1/receipts/export/formats` | `getExportFormats()` | — | `{ formats: ExportFormat[] }` |
| GET | `/api/v1/receipts/export/{format}` | `exportReceipts(format, params)` | query: date_from, date_to, category | CSV blob |

#### Work Queue
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/work-queue` | `getWorkQueue(limit?)` | query: limit? | `{ items: WorkQueueItem[] }` |

#### Dashboard
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/dashboard` | `getDashboard()` | — | `DashboardData` |

#### Jobs
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/jobs` | `getJobs()` | — | `{ items: Job[] }` |
| POST | `/product/jobs/{id}/retry` | `retryJob(id)` | — | `Job` |
| POST | `/product/jobs/{id}/cancel` | `cancelJob(id)` | — | `Job` |

#### Privacy
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/privacy/export` | `exportPrivacyData()` | — | JSON blob |
| PUT | `/product/privacy/retention` | `setRetention(days)` | `{ retention_days }` | `{ retention_days }` |
| POST | `/product/privacy/purge` | `purgeExpired()` | — | `{ purged }` |

#### Preferences
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/preferences` | `getPreferences()` | — | `Preferences` |
| PUT | `/product/preferences` | `savePreferences(payload)` | `{ payload: {...} }` | `Preferences` |

#### Batch Processing
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| POST | `/api/v1/receipts/batch` | `batchUpload(files, lang?)` | FormData (files) or `{ image_urls }` | `{ job_id, status, total }` |
| GET | `/api/v1/receipts/batch/{id}` | `getBatchStatus(id)` | — | `BatchJob` |

#### Forecast
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/forecasts` | `getForecast(params)` | query: period, category?, horizon, date_from?, date_to? | `ForecastResult` |
| GET | `/forecasts/anomalies` | `getAnomalies(params)` | query: period, method, threshold, date_from?, date_to? | `AnomalyResult` |
| GET | `/forecasts/budget-variance` | `getBudgetVariance(params)` | query: period?, horizon | `BudgetVarianceResult` |

#### Accounting
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/approval-flows` | `getApprovalFlows()` | — | `{ items: ApprovalFlow[] }` |
| POST | `/product/approval-flows` | `createApprovalFlow(body)` | `{ name, definition }` | `ApprovalFlow` |
| POST | `/product/approval-flows/simulate` | `simulateApprovalFlow(def, receipt)` | `{ definition, receipt }` | simulation result |
| GET | `/product/inbound-emails` | `getInboundEmails()` | — | `{ items: InboundEmail[], address }` |
| POST | `/product/inbound-emails` | `receiveEmail(body)` | `{ sender, subject, attachments }` | result |
| GET | `/product/recurring-expenses` | `getRecurringExpenses()` | — | `{ items: RecurringExpense[] }` |
| POST | `/product/recurring-expenses/feedback` | `submitRecurringFeedback(body)` | `{ merchant, is_subscription }` | result |
| POST | `/product/exchange-rates` | `setExchangeRate(body)` | `{ base, quote, rate, rate_date, source }` | rate |
| POST | `/product/currency/convert` | `convertCurrency(body)` | `{ amount, base, quote, rate_date? }` | `{ converted, quote, rate }` |
| GET | `/product/permissions` | `getPermissions()` | — | `PermissionMatrix` |
| PUT | `/product/permissions` | `updatePermissions(body)` | `{ role, permissions }` | result |

#### Diagnostics
| Method | Endpoint | Client Function | Request | Response |
|--------|----------|----------------|---------|----------|
| GET | `/product/diagnostics` | `getDiagnostics()` | — | `Diagnostics` |
| GET | `/product/diagnostics/bundle` | `downloadDiagnostics()` | — | ZIP blob |

---

## 12. PWA & Offline Strategy

Following mealmind patterns:
- **Service Worker**: `@serwist/next` for caching static assets and API responses
- **Offline Indicator**: Network state badge in topbar
- **Install Prompt**: "Install App" button when `beforeinstallprompt` fires
- **Manifest**: Dynamic `manifest.ts` route generating web app manifest
- **Cache Strategy**: Cache-first for static assets, network-first for API calls

---

## 13. Key Design Decisions

1. **No Zustand/Redux**: The app is server-driven. SWR handles all data fetching/caching. Local component state suffices for UI interactions.

2. **English-First i18n**: All hardcoded strings in the codebase are English. Hungarian translations are a follow-up task. The `t()` function and message catalog are ready for any locale.

3. **Server Components by Default**: Every page that reads data is a Server Component. Only interactive widgets are `"use client"`.

4. **Tailwind CSS**: Replaces the monolithic `workspace.css`. Provides consistent spacing, colors, and responsive utilities. Custom design tokens via `tailwind.config.ts` match the current color scheme.

5. **Typed API Client**: Every endpoint has a strongly-typed function with request/response types. No `any` types in the API layer.

6. **Mobile-First**: All layouts work on 320px width. Desktop enhancements layer on top via Tailwind responsive prefixes.

7. **Multi-Tenant Header Auth**: Tenant and role are sent as HTTP headers (`X-Tenant-ID`, `X-Role`). No complex auth flow needed for the MVP — the login page is a simple tenant/role selector.

8. **Preserve All Features**: Every feature in the current `workspace.js` (125 lines, ~55KB) is mapped to a route/component in the new architecture. No feature is dropped.

---

## 14. Dependencies

```json
{
  "dependencies": {
    "next": "^14.2.35",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "swr": "^2.2.5",
    "@serwist/next": "^9.5.12",
    "serwist": "^9.5.12",
    "recharts": "^3.10.1"
  },
  "devDependencies": {
    "typescript": "^5.9.3",
    "@types/node": "^20.19.43",
    "@types/react": "^18.3.31",
    "@types/react-dom": "^18.3.7",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20",
    "@playwright/test": "^1.62.1",
    "axe-core": "^4.12.1"
  }
}
```

---

## 15. Task Breakdown (P0/P1/P2)

### P0 — Core Infrastructure (must ship first)

| # | Task | Description | Depends On |
|---|------|-------------|------------|
| P0-1 | Initialize Next.js project | `npx create-next-app` with TypeScript, Tailwind, App Router. Configure `next.config.ts`, `tailwind.config.ts`, `tsconfig.json`. | — |
| P0-2 | Define TypeScript types | Create `lib/types.ts` with all interfaces from §6. | — |
| P0-3 | Build typed API client | Create `lib/api.ts` with `request()`, `tenantRequest()`, `uploadWithProgress()`, `ApiError`. Map all endpoints from §11. | P0-2 |
| P0-4 | Create AppShell layout | `AppShell.tsx`, `Sidebar.tsx`, `MobileNav.tsx`, `Topbar.tsx` with navigation items from §2. | P0-1 |
| P0-5 | Build shared components | `EmptyState`, `ConfidenceBadge`, `StatusBadge`, `Money`, `Pagination`, `FilterBar`, `Toast`, `Modal`. | P0-1 |
| P0-6 | Implement i18n system | `lib/i18n.ts` with en/hu message catalogs. `t()` function and locale persistence. | P0-1 |
| P0-7 | Dashboard page | KPI grid, next actions, spending chart, quality panel, trust panel. Uses `getDashboard()`, `searchReceipts()`, `getApprovals()`, `getWorkQueue()`. | P0-3, P0-4, P0-5 |
| P0-8 | Upload page | DropZone, UploadQueue, file upload with progress. Uses `uploadReceipt()`. | P0-3, P0-4, P0-5 |

### P1 — Core Workflows (ship after P0)

| # | Task | Description | Depends On |
|---|------|-------------|------------|
| P1-1 | Receipts list page | Filtered table with search, status/readiness/tag/amount filters, saved views, bulk selection, pagination. Uses `searchReceipts()`, `getSavedViews()`. | P0-3, P0-4, P0-5 |
| P1-2 | Receipt detail page | Metadata editing, history timeline, validation status, line item editor, OCR box overlay, image viewer. | P0-3, P0-4, P0-5 |
| P1-3 | Review workspace | Side-by-side image + form, confidence badges, zoom/rotate, source/structured toggle, save/complete actions. Uses `getReviewItems()`, `updateReceiptWorkspace()`. | P0-3, P0-4, P0-5 |
| P1-4 | Approvals page | Approval cards with approve/reject dialogs, policy creation. Uses `getApprovals()`, `decideApproval()`, `createApprovalPolicy()`. | P0-3, P0-4, P0-5 |
| P1-5 | Duplicates page | Side-by-side comparison cards, same/different decision. Uses `getDuplicates()`, `decideDuplicate()`. | P0-3, P0-4, P0-5 |
| P1-6 | Automations page | Rule cards, create/preview rules. Uses `getRules()`, `createRule()`, `previewRule()`. | P0-3, P0-4, P0-5 |
| P1-7 | Accounting page | Receipt selector, validation display, line item editor, field link map. Uses `validateReceipt()`, `updateLineItems()`, `getReceiptBoxes()`. | P0-3, P0-4, P0-5 |

### P2 — Supporting Features (ship after P1)

| # | Task | Description | Depends On |
|---|------|-------------|------------|
| P2-1 | Export center | Connection cards, export history, connection creation/testing. | P0-3, P0-4 |
| P2-2 | Export preparation | Receipt selection for export, validation check, blocked/warnings display. | P2-1 |
| P2-3 | Inbox page | Inbound email list, simulated email sending. | P0-3, P0-4 |
| P2-4 | Subscriptions page | Recurring expense cards, subscription feedback. | P0-3, P0-4 |
| P2-5 | Forecast page | Forecast cards, anomaly table, budget variance projections. Uses `getForecast()`, `getAnomalies()`, `getBudgetVariance()`. | P0-3, P0-4 |
| P2-6 | Reports page | Spending charts, export history, category breakdown. | P0-3, P0-4 |
| P2-7 | Settings pages | Profile/preferences, members, permissions matrix, privacy (retention, purge, export), diagnostics. | P0-3, P0-4 |
| P2-8 | Notification panel | Slide-over panel with read/archive actions, unread count badge. | P0-3, P0-4 |
| P2-9 | Onboarding flow | First-run modal with guided steps, skip option, preference saving. | P0-3, P0-4 |
| P2-10 | PWA setup | Service worker, manifest, install prompt, offline indicator. | P0-1 |
| P2-11 | Batch processing UI | Multi-file upload with parallel processing, progress polling. | P0-8 |
| P2-12 | Login page | Tenant/role selector with persistent preferences. | P0-4 |
| P2-13 | E2E tests | Playwright tests for critical flows: upload → review → approve → export. | All P0/P1 |
