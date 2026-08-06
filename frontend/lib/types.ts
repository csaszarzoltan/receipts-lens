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
// Review
// ---------------------------------------------------------------------------

export interface ReviewItem {
  receipt_id: string;
  receipt: Receipt;
  version: number;
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

export interface PermissionMatrix {
  roles: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// Preferences / Onboarding
// ---------------------------------------------------------------------------

export interface Preferences {
  language: string;
  compact: boolean;
  high_contrast: boolean;
  onboarding_done: boolean;
  dashboard_widgets?: string[];
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
