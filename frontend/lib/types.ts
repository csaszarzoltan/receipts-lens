/**
 * ReceiptLens — TypeScript data models.
 *
 * These interfaces mirror the FastAPI response schemas so the typed API
 * client (lib/api.ts) never needs `any`. Field names follow the backend's
 * snake_case wire format.
 */

// ---------------------------------------------------------------------------
// Core Receipt
// ---------------------------------------------------------------------------

export interface LineItem {
  name: string;
  price: number;
  quantity?: number;
  unit_price?: number;
  amount?: number;
  category?: string | null;
}

/**
 * Which extraction pipeline produced a result: the LLM vision path or the
 * classic Tesseract OCR path.
 */
export type OcrSource = "vision" | "tesseract";

/**
 * One extraction result from the AI-mode flow (the `ai_result` /
 * `tesseract_result` payloads). Mirrors the backend's ConfidenceReceipt
 * shape so the UI can render and compare both pipelines on the same image.
 */
export interface AiExtraction {
  merchant: string | null;
  date: string | null;
  total: number | null;
  tax: number | null;
  currency: string | null;
  line_items: LineItem[];
  /** Per-field confidence, e.g. { merchant: 0.97, date: 0.92, total: 0.99 } */
  confidence: Record<string, number>;
  /** Per-receipt OCR confidence band (high/medium/low). */
  confidence_level?: ConfidenceLevel | null;
}

/**
 * Response of the AI-mode upload (`ai_scan=true`). Always carries the
 * `source` that produced the primary result; when AI mode is enabled the
 * response also exposes both pipelines so the user can compare.
 */
export interface AiScanUploadResponse extends ReceiptItem {
  source: OcrSource;
  ai_result?: AiExtraction;
  tesseract_result?: AiExtraction;
}

/** Per-receipt OCR confidence band — how much the extraction can be trusted. */
export type ConfidenceLevel = "high" | "medium" | "low";

export interface Receipt {
  vendor: string;
  total: number | null;
  date: string | null;
  tax: number | null;
  currency: string | null;
  /** Where the currency came from; "user" once someone set it by hand. */
  currency_source?: CurrencySource | null;
  /** True when the currency was not printed on the receipt and was guessed. */
  currency_assumed?: boolean;
  /** The total OCR read while the confidence gate withholds `total`. */
  total_candidate?: number | null;
  /** True once the stored image was read again for a total candidate. */
  total_candidate_checked?: boolean;
  line_items: LineItem[];
  confidence: Record<string, number>;
  confidence_level?: ConfidenceLevel | null;
  category?: string;
}

export type CurrencySource =
  | "marker"
  | "default"
  | "inferred_merchant"
  | "inferred_tenant"
  | "user";

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

export interface ReceiptItem {
  receipt_id: string;
  receipt: Receipt;
  metadata: ReceiptMetadata | null;
  status: ReceiptStatus;
  version: number;
  readiness: ReadinessInfo;
  created_at: string;
}

export interface PagedReceipts {
  items: ReceiptItem[];
  total: number;
  offset: number;
  limit: number;
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Consumer dashboard (F1.2 — docs/plans/consumer-pivot-2026-08-13.md §3.4)
// ---------------------------------------------------------------------------

export interface DailyRemaining {
  budgeted: number;
  spent_this_month: number;
  remaining_this_month: number;
  days_left: number;
  daily_remaining: number;
  currency: string;
  pct_used: number;
}

export interface CategorySpend {
  key: string;
  label: string;
  total: number;
  count: number;
  pct: number;
}

export interface MonthlyByCategory {
  month: string;
  total_spent: number;
  currency: string;
  categories: CategorySpend[];
  other_currency_totals?: Record<string, number>;
  unpriced_receipts?: number;
}

export interface PriceAlert {
  merchant: string;
  amount: number;
  currency: string;
  monthly_cost: number;
  renewal_date: string;
  message: string;
}

export interface CancellableSubscription {
  id: string;
  merchant: string;
  amount: number;
  monthly_cost: number;
  annualized: number;
  renewal_date: string;
  frequency: "monthly" | "quarterly" | "annual";
  trend: SubscriptionTrend;
  price_increase: boolean;
  /** Currency of the receipts behind this subscription; null when it was not printed. */
  currency?: string | null;
}

export interface HouseholdMember {
  member_id: string;
  email: string;
  role: string;
  role_label: string;
}

export interface HouseholdStatus {
  shared_budget: number;
  spent: number;
  remaining: number;
  currency: string;
  members: HouseholdMember[];
  member_breakdown_note?: string | null;
  /** Spend in other currencies this month; not converted, so shown separately. */
  spent_other_currencies?: Record<string, number>;
  /** Receipts this month that could not be priced (no total or no currency). */
  unpriced_receipts?: number;
}

export interface RecentReceipt {
  receipt_id: string;
  merchant: string;
  total: number;
  currency: string;
  date: string;
  status: string;
  confidence_level?: ConfidenceLevel | null;
}

export interface SavingsCandidate {
  merchant: string;
  potential_saving: number;
  delta_pct: number;
}

export interface SavingsBlock {
  period: string;
  potential_saving: number;
  total_spent: number;
  avg_by_category: Record<string, number>;
  currency: string;
  top_candidates: SavingsCandidate[];
  savings_candidates?: SavingsCandidate[];
}

export interface ConsumerDashboard {
  generated_at: string;
  tenant: string;
  daily_remaining: DailyRemaining | null;
  monthly_by_category: MonthlyByCategory;
  price_alerts: PriceAlert[];
  cancellable_subscriptions: CancellableSubscription[];
  household: HouseholdStatus;
  recent_receipts: RecentReceipt[];
  savings: SavingsBlock;
}

// ---------------------------------------------------------------------------
// Review
// ---------------------------------------------------------------------------

export interface ReviewChecks {
  /** Sum of the priced line items, or null when there are none. */
  line_sum: number | null;
  /** Whether the lines add up to the amount; null when there is nothing to compare. */
  lines_match: boolean | null;
}

export interface ReviewItem {
  receipt_id: string;
  receipt: Receipt;
  version: number;
  checks?: ReviewChecks;
}

// ---------------------------------------------------------------------------
// Approvals
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Duplicates
// ---------------------------------------------------------------------------

export interface DuplicateCandidate {
  left_id: string;
  right_id: string;
  left: Receipt;
  right: Receipt;
  confidence: number;
}

// ---------------------------------------------------------------------------
// Automation Rules
// ---------------------------------------------------------------------------

export interface AutomationRule {
  rule_id: string;
  name: string;
  conditions: Record<string, unknown>;
  actions: Record<string, unknown>;
  priority: number;
  active: boolean;
}

// ---------------------------------------------------------------------------
// Connections / Integrations / Exports
// ---------------------------------------------------------------------------

export interface Connection {
  connection_id: string;
  name: string;
  provider: "csv" | "quickbooks" | "xero";
  mapping: Record<string, string>;
  active: boolean;
}

export interface ProviderConnection {
  connection_id: string;
  tenant_id: string;
  provider: string;
  provider_company_id: string;
  provider_company_name: string;
  health: string;
  reauthorization_required: boolean;
  created_at: string;
  last_tested_at: string | null;
}

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

export interface ExportFormat {
  name: string;
  columns: string[];
  delimiter: string;
}

// ---------------------------------------------------------------------------
// Accounting
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// Forecast
// ---------------------------------------------------------------------------

export interface ForecastEntry {
  category: string;
  next_period_total: number;
  confidence_low: number;
  confidence_high: number;
  trend: number;
  method: string;
}

export interface ForecastResult {
  period: string;
  currency: string;
  forecasts: ForecastEntry[];
  source_range: { date_from: string; date_to: string };
  narrative?: string;
}

export interface AnomalyEntry {
  period: string;
  category: string;
  expected: number;
  actual: number;
  score: number;
  flagged: boolean;
}

export interface AnomalyResult {
  method: string;
  threshold: number;
  anomalies: AnomalyEntry[];
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

export interface BudgetVarianceResult {
  currency: string;
  projections: BudgetProjection[];
}

// ---------------------------------------------------------------------------
// Work Queue / Notifications / Saved Views
// ---------------------------------------------------------------------------

export interface WorkQueueItem {
  title: string;
  reason: string;
  action_url: string;
  action_label: string;
}

export interface Notification {
  notification_id: string;
  title: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface SavedView {
  view_id: string;
  name: string;
  filters: Record<string, unknown>;
  shared: boolean;
  pinned: boolean;
}

// ---------------------------------------------------------------------------
// Members / Permissions
// ---------------------------------------------------------------------------

export interface Member {
  member_id: string;
  email: string;
  role: "admin" | "reviewer" | "integrator";
  active: boolean;
}

// ---------------------------------------------------------------------------
// F1.3 household auth — magic links, sessions, invites
// ---------------------------------------------------------------------------

/** Household role vocabulary (§3.2 of the consumer-pivot plan). */
export type HouseholdRole = "owner" | "adult" | "child" | "view_only";

/** Response of POST /auth/magic-link-request. */
export interface MagicLinkResponse {
  delivered: boolean;
  /** Dev-mode only (RECEIPTLENS_ENV != production): the raw one-time token. */
  token?: string;
  /** Dev-mode only: the full clickable login link. */
  magic_link?: string;
  email: string;
  expires_at: string;
}

/** Session identity returned by verify / accept / session-me. */
export interface SessionIdentity {
  session_token: string;
  email: string;
  household_id: string;
  role: HouseholdRole;
  expires_at: string;
  display_name?: string | null;
}

/** A household invite row (owner view + create response). */
export interface HouseholdInvite {
  invite_id: string;
  email: string;
  role: HouseholdRole;
  status: "pending" | "accepted";
  expires_at?: string;
  token?: string;
  magic_link?: string;
  delivered?: boolean;
}

export interface PermissionMatrix {
  roles: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// Preferences / Onboarding
// ---------------------------------------------------------------------------

export interface Preferences {
  language: string;
  base_currency: string;
  /** "saved" (chosen), "receipts" (what the receipts state) or "default" (nothing known yet). */
  base_currency_source?: "saved" | "receipts" | "default";
  compact: boolean;
  high_contrast: boolean;
  onboarding_done: boolean;
  dashboard_widgets?: string[];
  email_alerts?: boolean;
}

// ---------------------------------------------------------------------------
// Recurring Expenses / Inbound Emails
// ---------------------------------------------------------------------------

export interface RecurringExpense {
  merchant: string;
  annualized: number;
  occurrences: number;
  price_change: number;
  likely_subscription: boolean;
}

// ---------------------------------------------------------------------------
// Subscriptions (subscription intelligence layer)
// ---------------------------------------------------------------------------

export type SubscriptionTrend = "up" | "stable" | "down";

export interface Subscription {
  id: string;
  merchant: string;
  occurrences: number;
  frequency: "monthly" | "quarterly" | "annual";
  renewal_date: string;
  amount: number;
  monthly_cost: number;
  annualized: number;
  trend: SubscriptionTrend;
  price_increase: boolean;
  likely_subscription: boolean;
  currency?: string | null;
}

export interface SubscriptionSummary {
  total: number;
  /** Monthly cost in `currency` only; other currencies are listed separately, never added. */
  monthly_total: number;
  currency?: string | null;
  other_currency_totals?: Record<string, number>;
}

export interface SubscriptionListResponse {
  subscriptions: Subscription[];
  summary: SubscriptionSummary;
}

export interface CancelGuide {
  subscription_id: string;
  merchant: string;
  steps: string[];
  url: string | null;
}

export interface InboundEmail {
  sender: string;
  subject: string;
  attachments: Array<{ filename: string; content_type: string; size: number }>;
  status: string;
}

// ---------------------------------------------------------------------------
// Jobs / Batch
// ---------------------------------------------------------------------------

export interface Job {
  job_id: string;
  receipt_id: string;
  status: string;
  attempt: number;
  error: string | null;
  created_at: string;
}

export interface BatchJob {
  job_id: string;
  status: string;
  total: number;
  completed: number;
}

// ---------------------------------------------------------------------------
// Diagnostics / Exchange Rates
// ---------------------------------------------------------------------------

export interface Diagnostics {
  version: string;
  database: string;
  receipt_count: number;
  failed_jobs: number;
  pwa: boolean;
  ocr: string;
}

export interface ExchangeRate {
  base: string;
  quote: string;
  rate: number;
  rate_date: string;
  source: string;
}

// ---------------------------------------------------------------------------
// Approval Flows / Misc
// ---------------------------------------------------------------------------

export interface ApprovalFlow {
  flow_id: string;
  name: string;
  definition: Record<string, unknown>;
}

export interface ApiKeyResult {
  key_id: string;
  name: string;
  secret: string;
}

export interface WorkspaceVersion {
  version: number;
}

export interface LineItemsResult {
  line_items: LineItem[];
  version: number;
}

// ---------------------------------------------------------------------------
// Warranties and return deadlines
// ---------------------------------------------------------------------------

export type WarrantyStatus = "active" | "returned" | "claim" | "archived";

export interface Warranty {
  warranty_id: string;
  receipt_id: string | null;
  item_name: string;
  merchant: string | null;
  purchase_date: string;
  return_days: number;
  warranty_months: number;
  status: WarrantyStatus;
  notes: string | null;
  return_by: string | null;
  warranty_ends: string | null;
  /** Negative once the date has passed; null when there is no such deadline. */
  return_days_left: number | null;
  warranty_days_left: number | null;
  next_deadline: string | null;
  next_deadline_kind: "return" | "warranty" | null;
  days_to_next: number | null;
  due_soon: boolean;
}

export interface WarrantyList {
  items: Warranty[];
  summary: { active: number; due_soon: number };
}

export interface WarrantyInput {
  item_name: string;
  merchant?: string;
  purchase_date: string;
  return_days: number;
  warranty_months: number;
  receipt_id?: string;
  notes?: string;
}

// ---------------------------------------------------------------------------
// Statement check
// ---------------------------------------------------------------------------

export interface StatementLine {
  row: number;
  date: string;
  amount: number;
  description: string;
  currency: string | null;
}

export interface StatementReceipt {
  receipt_id: string;
  vendor: string | null;
  date: string;
  amount: number | null;
  confirmed: boolean;
  currency: string | null;
  version: number;
}

export interface StatementResult {
  assumptions: { direction: string; skipped_rows: number; date_order: string };
  period: { from: string | null; to: string | null };
  counts: { lines: number; matched: number; unmatched_lines: number; unmatched_receipts: number; suggestions: number };
  matched: Array<{ line: StatementLine; receipt: StatementReceipt; confirmed: boolean }>;
  suggestions: Array<{ line: StatementLine; receipt: StatementReceipt }>;
  unmatched_lines: StatementLine[];
  unmatched_receipts: StatementReceipt[];
}
