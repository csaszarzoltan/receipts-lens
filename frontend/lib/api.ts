/**
 * Typed API client for the ReceiptLens FastAPI backend.
 *
 * Every backend endpoint maps to one strongly-typed function — no `any`,
 * no mock data. Requests are issued against `API_BASE_URL`, which defaults
 * to the local FastAPI dev server and can be overridden at build time via
 * NEXT_PUBLIC_API_BASE_URL.
 *
 * Authentication is header-based (X-Tenant-ID / X-Role), attached by
 * `tenantRequest()`. File uploads use `uploadWithProgress()` (XHR-based)
 * so the UI can show real progress.
 */
import type {
  AiScanUploadResponse,
  AnomalyResult,
  ApiKeyResult,
  Approval,
  ApprovalFlow,
  ApprovalPolicy,
  AutomationRule,
  BatchJob,
  BudgetVarianceResult,
  CancelGuide,
  Connection,
  ConsumerDashboard,
  DashboardData,
  Diagnostics,
  DuplicateCandidate,
  ExportFormat,
  ExportPreparation,
  ExportRun,
  ForecastResult,
  HistoryEntry,
  SessionIdentity,
  MagicLinkResponse,
  HouseholdRole,
  HouseholdInvite,
  InboundEmail,
  Job,
  LineItem,
  LineItemsResult,
  Member,
  Notification,
  OCRBox,
  PagedReceipts,
  PermissionMatrix,
  Preferences,
  ProviderConnection,
  Receipt,
  ReceiptItem,
  RecurringExpense,
  ReviewItem,
  SavedView,
  SubscriptionListResponse,
  ValidationResult,
  WorkQueueItem,
  WorkspaceVersion,
} from "./types";
import { authHeaders, getSessionToken, clearSessionToken } from "./auth";
import { AI_SCAN_ENABLED } from "./featureFlags";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number;
  code?: string;
  retryable: boolean;
  retryAfterSeconds?: number;

  constructor(
    status: number,
    message: string,
    options: { code?: string; retryable?: boolean; retryAfterSeconds?: number } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = options.code;
    this.retryable = options.retryable ?? (status === 408 || status === 429 || status >= 500);
    this.retryAfterSeconds = options.retryAfterSeconds;
  }
}

function parseErrorBody(body: unknown): { message?: string; code?: string } {
  if (body && typeof body === "object") {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return { message: detail };
    if (detail && typeof detail === "object") {
      const d = detail as { message?: unknown; code?: unknown };
      return {
        message: typeof d.message === "string" ? d.message : undefined,
        code: typeof d.code === "string" ? d.code : undefined,
      };
    }
  }
  return {};
}

async function throwForStatus(res: Response): Promise<never> {
  let message = `Request failed with status ${res.status}`;
  let code: string | undefined;
  try {
    const parsed = parseErrorBody(await res.json());
    if (parsed.message) message = parsed.message;
    code = parsed.code;
  } catch {
    // non-JSON body — keep generic message
  }
  const retryHeader = res.headers.get("Retry-After");
  const parsedRetry = retryHeader ? Number(retryHeader) : undefined;
  throw new ApiError(res.status, message, {
    code,
    retryAfterSeconds: Number.isFinite(parsedRetry) ? parsedRetry : undefined,
  });
}

// ---------------------------------------------------------------------------
// Core request helpers
// ---------------------------------------------------------------------------

/** Core request helper (exported for custom callers and tests). */
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  if (!res.ok) await throwForStatus(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Request with tenant/role headers attached (the default for product APIs). */
export function tenantRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  return request<T>(path, {
    ...options,
    headers: {
      ...authHeaders(),
      ...options.headers,
    },
  });
}

/** Binary-safe request (no JSON content-type), used for blobs/downloads. */
async function binaryRequest(path: string, options: RequestInit = {}): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...options.headers,
    },
  });
  if (!res.ok) await throwForStatus(res);
  return res.blob();
}

/**
 * File upload with progress events (XMLHttpRequest-based, matching the
 * architecture spec) — FormData posts to a multipart endpoint.
 * `formFields` are appended to the FormData payload (e.g. `ai_scan`).
 */
export function uploadWithProgress<T>(
  path: string,
  file: File,
  onProgress?: (percent: number) => void,
  formFields?: Record<string, string>,
): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}${path}`);
    for (const [key, value] of Object.entries(authHeaders())) {
      xhr.setRequestHeader(key, value);
    }
    xhr.upload.onprogress = (event) => {
      if (onProgress && event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as T);
        } catch {
          resolve(undefined as T);
        }
      } else {
        let message = `Upload failed with status ${xhr.status}`;
        try {
          const parsed = parseErrorBody(JSON.parse(xhr.responseText));
          if (parsed.message) message = parsed.message;
        } catch {
          // keep generic message
        }
        reject(new ApiError(xhr.status, message));
      }
    };
    xhr.onerror = () => reject(new ApiError(0, "Network error during upload"));
    const form = new FormData();
    form.append("file", file);
    if (formFields) {
      for (const [key, value] of Object.entries(formFields)) {
        form.append(key, value);
      }
    }
    xhr.send(form);
  });
}

function qs(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const raw = search.toString();
  return raw ? `?${raw}` : "";
}

// ---------------------------------------------------------------------------
// Health & Platform
// ---------------------------------------------------------------------------

export async function getHealth(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}

export async function getReadiness(): Promise<{ status: string; dependencies?: unknown }> {
  return request<{ status: string; dependencies?: unknown }>("/ready");
}

export async function getCapabilities(): Promise<{
  schema_version: string;
  requirements: unknown;
}> {
  return request<{ schema_version: string; requirements: unknown }>(
    "/api/v1/platform/capabilities",
  );
}

// ---------------------------------------------------------------------------
// Receipt CRUD
// ---------------------------------------------------------------------------

export async function uploadReceipt(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<ReceiptItem & { applied_rules?: unknown }> {
  return uploadWithProgress<ReceiptItem & { applied_rules?: unknown }>(
    "/product/receipts/upload",
    file,
    onProgress,
  );
}

/**
 * AI-mode upload: posts `ai_scan=true` so the backend runs the LLM vision
 * path (with automatic Tesseract fallback). The response carries `source`
 * plus, in AI mode, `ai_result` and `tesseract_result` for comparison.
 *
 * Production gate: throws when NEXT_PUBLIC_AI_SCAN_ENABLED was not enabled
 * at build time — no caller (UI, hook or console) can trigger vision OCR
 * from a build where the feature is off.
 */
export async function uploadReceiptWithAi(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<AiScanUploadResponse> {
  if (!AI_SCAN_ENABLED) {
    throw new ApiError(403, "AI Scan is coming soon — part of the Pro plan.");
  }
  return uploadWithProgress<AiScanUploadResponse>(
    "/product/receipts/upload",
    file,
    onProgress,
    { ai_scan: "true" },
  );
}

export interface SearchReceiptsParams {
  query?: string;
  status?: string;
  tag?: string;
  min_total?: number;
  max_total?: number;
  limit?: number;
  offset?: number;
  readiness?: string;
}

export async function searchReceipts(
  params: SearchReceiptsParams = {},
): Promise<PagedReceipts> {
  return tenantRequest<PagedReceipts>(
    `/product/receipts${qs({
      query: params.query,
      status: params.status,
      tag: params.tag,
      min_total: params.min_total,
      max_total: params.max_total,
      limit: params.limit,
      offset: params.offset,
      readiness: params.readiness,
    })}`,
  );
}

export async function getReceipt(receiptId: string): Promise<ReceiptItem> {
  return tenantRequest<ReceiptItem>(
    `/product/receipts/${encodeURIComponent(receiptId)}`,
  );
}

export async function getReceiptImage(receiptId: string): Promise<Blob> {
  return binaryRequest(`/product/receipts/${encodeURIComponent(receiptId)}/image`);
}

export async function getReceiptBoxes(
  receiptId: string,
): Promise<{ receipt_id: string; boxes: OCRBox[] }> {
  return tenantRequest<{ receipt_id: string; boxes: OCRBox[] }>(
    `/product/receipts/${encodeURIComponent(receiptId)}/ocr-boxes`,
  );
}

export async function getReceiptHistory(
  receiptId: string,
): Promise<{ items: HistoryEntry[] }> {
  return tenantRequest<{ items: HistoryEntry[] }>(
    `/product/receipts/${encodeURIComponent(receiptId)}/history`,
  );
}

export async function validateReceipt(
  receiptId: string,
  connectionId?: string,
): Promise<ValidationResult> {
  return tenantRequest<ValidationResult>(
    `/product/receipts/${encodeURIComponent(receiptId)}/validation${qs({
      connection_id: connectionId,
    })}`,
  );
}

export async function updateMetadata(
  receiptId: string,
  body: { tags: string[]; project: string | null; cost_center: string | null },
): Promise<ReceiptItem> {
  return tenantRequest<ReceiptItem>(
    `/product/receipts/${encodeURIComponent(receiptId)}/metadata`,
    { method: "PUT", body: JSON.stringify(body) },
  );
}

export async function updateReceiptWorkspace(
  receiptId: string,
  body: {
    fields?: Record<string, unknown>;
    line_items?: LineItem[];
    metadata?: Record<string, unknown>;
    action?: "save" | "complete";
  },
  version: number,
): Promise<WorkspaceVersion> {
  return tenantRequest<WorkspaceVersion>(
    `/product/receipts/${encodeURIComponent(receiptId)}/workspace`,
    {
      method: "PATCH",
      headers: { "If-Match": String(version) },
      body: JSON.stringify(body),
    },
  );
}

export async function updateLineItems(
  receiptId: string,
  items: LineItem[],
  version: number,
): Promise<LineItemsResult> {
  return tenantRequest<LineItemsResult>(
    `/product/receipts/${encodeURIComponent(receiptId)}/line-items`,
    {
      method: "PUT",
      headers: { "If-Match": String(version) },
      body: JSON.stringify({ items, expected_version: version }),
    },
  );
}

// ---------------------------------------------------------------------------
// Review Items
// ---------------------------------------------------------------------------

export async function getReviewItems(): Promise<{ items: ReviewItem[] }> {
  return tenantRequest<{ items: ReviewItem[] }>("/product/review-items");
}

export async function correctReceipt(
  receiptId: string,
  body: { changes: Record<string, unknown>; action?: "save" | "complete" },
  version: number,
): Promise<ReviewItem> {
  return tenantRequest<ReviewItem>(`/product/review-items/${encodeURIComponent(receiptId)}`, {
    method: "PATCH",
    headers: { "If-Match": String(version) },
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Approvals
// ---------------------------------------------------------------------------

export async function getApprovals(
  status?: string,
): Promise<{ items: Approval[] }> {
  return tenantRequest<{ items: Approval[] }>(
    `/product/approvals${qs({ status })}`,
  );
}

export async function decideApproval(
  approvalId: string,
  decision: "approved" | "rejected",
  note?: string,
): Promise<Approval> {
  return tenantRequest<Approval>(
    `/product/approvals/${encodeURIComponent(approvalId)}/decision`,
    { method: "POST", body: JSON.stringify({ decision, note }) },
  );
}

export async function createApprovalPolicy(body: {
  name: string;
  threshold: number;
  currency: string;
}): Promise<ApprovalPolicy> {
  return tenantRequest<ApprovalPolicy>("/product/approval-policies", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function requestApproval(receiptId: string): Promise<Approval> {
  return tenantRequest<Approval>(
    `/product/receipts/${encodeURIComponent(receiptId)}/approval`,
    { method: "POST" },
  );
}

// ---------------------------------------------------------------------------
// Duplicates
// ---------------------------------------------------------------------------

export async function getDuplicates(): Promise<{ items: DuplicateCandidate[] }> {
  return tenantRequest<{ items: DuplicateCandidate[] }>("/product/duplicates");
}

export async function decideDuplicate(
  leftId: string,
  rightId: string,
  decision: string,
): Promise<{ status: string }> {
  return tenantRequest<{ status: string }>("/product/duplicates/decision", {
    method: "POST",
    body: JSON.stringify({ left_id: leftId, right_id: rightId, decision }),
  });
}

// ---------------------------------------------------------------------------
// Automation Rules
// ---------------------------------------------------------------------------

export async function getRules(): Promise<{ items: AutomationRule[] }> {
  return tenantRequest<{ items: AutomationRule[] }>("/product/automation-rules");
}

export async function createRule(body: {
  name: string;
  conditions: Record<string, unknown>;
  actions: Record<string, unknown>;
  priority: number;
}): Promise<AutomationRule> {
  return tenantRequest<AutomationRule>("/product/automation-rules", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function previewRule(
  conditions: Record<string, unknown>,
): Promise<{ matching_receipts: unknown }> {
  return tenantRequest<{ matching_receipts: unknown }>("/product/automation-rules/preview", {
    method: "POST",
    body: JSON.stringify({ conditions }),
  });
}

// ---------------------------------------------------------------------------
// Saved Views
// ---------------------------------------------------------------------------

export async function getSavedViews(): Promise<{ items: SavedView[] }> {
  return tenantRequest<{ items: SavedView[] }>("/product/saved-views");
}

export async function createSavedView(body: {
  name: string;
  filters: Record<string, unknown>;
  shared: boolean;
  pinned: boolean;
}): Promise<SavedView> {
  return tenantRequest<SavedView>("/product/saved-views", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function deleteSavedView(viewId: string): Promise<{ status: string; view_id: string }> {
  return tenantRequest<{ status: string; view_id: string }>(
    `/product/saved-views/${encodeURIComponent(viewId)}`,
    { method: "DELETE" },
  );
}

// ---------------------------------------------------------------------------
// Notifications
// ---------------------------------------------------------------------------

export async function getNotifications(
  includeArchived?: boolean,
): Promise<{ items: Notification[]; unread_count: number }> {
  return tenantRequest<{ items: Notification[]; unread_count: number }>(
    `/product/notifications${qs({ include_archived: includeArchived })}`,
  );
}

export async function updateNotification(
  notificationId: string,
  body: { read?: boolean; archived?: boolean },
): Promise<Notification> {
  return tenantRequest<Notification>(
    `/product/notifications/${encodeURIComponent(notificationId)}`,
    { method: "PATCH", body: JSON.stringify(body) },
  );
}

export async function markAllRead(): Promise<{ updated: number }> {
  return tenantRequest<{ updated: number }>("/product/notifications/read-all", {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Members & API Keys
// ---------------------------------------------------------------------------

export async function getMembers(): Promise<{ items: Member[] }> {
  return tenantRequest<{ items: Member[] }>("/product/members");
}

export async function addMember(body: { email: string; role: string }): Promise<Member> {
  return tenantRequest<Member>("/product/members", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function createApiKey(body: { name: string }): Promise<ApiKeyResult> {
  return tenantRequest<ApiKeyResult>("/product/api-keys", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Connections / Integrations
// ---------------------------------------------------------------------------

export async function getConnections(): Promise<{ items: Connection[] }> {
  return tenantRequest<{ items: Connection[] }>("/product/connections");
}

export async function createConnection(body: {
  name: string;
  provider: string;
  mapping: Record<string, string>;
}): Promise<Connection> {
  return tenantRequest<Connection>("/product/connections", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function testConnection(connectionId: string): Promise<Record<string, unknown>> {
  return tenantRequest<Record<string, unknown>>(
    `/product/connections/${encodeURIComponent(connectionId)}/test`,
    { method: "POST" },
  );
}

// --- QuickBooks Online connected workflow (OAuth lifecycle) ----------------

export async function getProviderConnections(): Promise<{ items: ProviderConnection[] }> {
  return tenantRequest<{ items: ProviderConnection[] }>("/product/provider-connections");
}

export async function getProviderConnection(connectionId: string): Promise<ProviderConnection> {
  return tenantRequest<ProviderConnection>(
    `/product/provider-connections/${encodeURIComponent(connectionId)}`,
  );
}

export async function refreshProviderConnection(connectionId: string): Promise<{ status: string }> {
  return tenantRequest<{ status: string }>(
    `/product/connections/${encodeURIComponent(connectionId)}/refresh`,
    { method: "POST" },
  );
}

export async function disconnectProviderConnection(connectionId: string): Promise<Record<string, unknown>> {
  return tenantRequest<Record<string, unknown>>(
    `/product/connections/${encodeURIComponent(connectionId)}/disconnect`,
    { method: "POST" },
  );
}

export async function startQuickBooksOAuth(): Promise<{ authorization_url: string; state_expires_at: string }> {
  return tenantRequest<{ authorization_url: string; state_expires_at: string }>(
    "/product/connections/quickbooks/oauth/start",
    { method: "POST", body: JSON.stringify({ return_path: "/integrations" }) },
  );
}


// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export async function createExport(body: {
  connection_id: string;
  receipt_ids: string[];
}): Promise<ExportRun> {
  return tenantRequest<ExportRun>("/product/exports", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getExportRuns(): Promise<{ items: ExportRun[] }> {
  return tenantRequest<{ items: ExportRun[] }>("/product/export-runs");
}

export async function prepareExport(body: {
  receipt_ids: string[];
  connection_id?: string;
}): Promise<ExportPreparation> {
  return tenantRequest<ExportPreparation>("/product/export-preparations", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getExportPreparations(): Promise<{ items: unknown[] }> {
  return tenantRequest<{ items: unknown[] }>("/product/export-preparations");
}

export async function getExportFormats(): Promise<{ formats: ExportFormat[] }> {
  return request<{ formats: ExportFormat[] }>("/api/v1/receipts/export/formats");
}

export async function exportReceipts(
  format: string,
  params: { date_from?: string; date_to?: string; category?: string } = {},
): Promise<Blob> {
  return binaryRequest(
    `/api/v1/receipts/export/${encodeURIComponent(format)}${qs(params)}`,
  );
}

// ---------------------------------------------------------------------------
// Work Queue & Dashboard
// ---------------------------------------------------------------------------

export async function getWorkQueue(
  limit?: number,
): Promise<{ items: WorkQueueItem[] }> {
  return tenantRequest<{ items: WorkQueueItem[] }>(
    `/product/work-queue${qs({ limit })}`,
  );
}

export async function getDashboard(): Promise<DashboardData> {
  return tenantRequest<DashboardData>("/product/dashboard");
}

// ---------------------------------------------------------------------------
// Consumer dashboard (F1.2 — §3.4 of docs/plans/consumer-pivot-2026-08-13.md)
// ---------------------------------------------------------------------------

export async function getConsumerDashboard(): Promise<ConsumerDashboard> {
  return tenantRequest<ConsumerDashboard>("/api/v1/consumer/dashboard");
}

// ---------------------------------------------------------------------------
// Jobs
// ---------------------------------------------------------------------------

export async function getJobs(): Promise<{ items: Job[] }> {
  return tenantRequest<{ items: Job[] }>("/product/jobs");
}

export async function retryJob(jobId: string): Promise<Job> {
  return tenantRequest<Job>(`/product/jobs/${encodeURIComponent(jobId)}/retry`, {
    method: "POST",
  });
}

export async function cancelJob(jobId: string): Promise<Job> {
  return tenantRequest<Job>(`/product/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Privacy
// ---------------------------------------------------------------------------

export async function exportPrivacyData(): Promise<unknown> {
  return tenantRequest<unknown>("/product/privacy/export");
}

export async function setRetention(days: number): Promise<{ retention_days: number }> {
  return tenantRequest<{ retention_days: number }>("/product/privacy/retention", {
    method: "PUT",
    body: JSON.stringify({ retention_days: days }),
  });
}

export async function purgeExpired(): Promise<{ purged: number }> {
  return tenantRequest<{ purged: number }>("/product/privacy/purge", {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Preferences
// ---------------------------------------------------------------------------

export async function getPreferences(): Promise<Preferences> {
  return tenantRequest<Preferences>("/product/preferences");
}

export async function savePreferences(
  payload: Partial<Preferences>,
): Promise<Preferences> {
  return tenantRequest<Preferences>("/product/preferences", {
    method: "PUT",
    body: JSON.stringify({ payload }),
  });
}

// ---------------------------------------------------------------------------
// Batch Processing
// ---------------------------------------------------------------------------

export async function batchUpload(
  files: File[],
  lang?: string,
  onProgress?: (percent: number) => void,
): Promise<BatchJob> {
  return new Promise<BatchJob>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE_URL}/api/v1/receipts/batch`);
    for (const [key, value] of Object.entries(authHeaders())) {
      xhr.setRequestHeader(key, value);
    }
    xhr.upload.onprogress = (event) => {
      if (onProgress && event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as BatchJob);
        } catch {
          reject(new ApiError(xhr.status, "Invalid batch response"));
        }
      } else {
        reject(new ApiError(xhr.status, `Batch upload failed with status ${xhr.status}`));
      }
    };
    xhr.onerror = () => reject(new ApiError(0, "Network error during batch upload"));
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    if (lang) form.append("lang", lang);
    xhr.send(form);
  });
}

export async function getBatchStatus(jobId: string): Promise<BatchJob> {
  return tenantRequest<BatchJob>(`/api/v1/receipts/batch/${encodeURIComponent(jobId)}`);
}

// ---------------------------------------------------------------------------
// Forecast
// ---------------------------------------------------------------------------

export interface ForecastParams {
  period?: string;
  category?: string;
  horizon?: number;
  date_from?: string;
  date_to?: string;
}

export async function getForecast(params: ForecastParams = {}): Promise<ForecastResult> {
  return request<ForecastResult>(
    `/forecasts${qs({
      period: params.period,
      category: params.category,
      horizon: params.horizon,
      date_from: params.date_from,
      date_to: params.date_to,
    })}`,
  );
}

export interface AnomalyParams {
  period?: string;
  method?: string;
  threshold?: number;
  date_from?: string;
  date_to?: string;
}

export async function getAnomalies(params: AnomalyParams = {}): Promise<AnomalyResult> {
  return request<AnomalyResult>(
    `/forecasts/anomalies${qs({
      period: params.period,
      method: params.method,
      threshold: params.threshold,
      date_from: params.date_from,
      date_to: params.date_to,
    })}`,
  );
}

export interface BudgetVarianceParams {
  period?: string;
  horizon?: number;
}

export async function getBudgetVariance(
  params: BudgetVarianceParams = {},
): Promise<BudgetVarianceResult> {
  return request<BudgetVarianceResult>(
    `/forecasts/budget-variance${qs({
      period: params.period,
      horizon: params.horizon,
    })}`,
  );
}

// ---------------------------------------------------------------------------
// Accounting
// ---------------------------------------------------------------------------

export async function getApprovalFlows(): Promise<{ items: ApprovalFlow[] }> {
  return tenantRequest<{ items: ApprovalFlow[] }>("/product/approval-flows");
}

export async function createApprovalFlow(body: {
  name: string;
  definition: Record<string, unknown>;
}): Promise<ApprovalFlow> {
  return tenantRequest<ApprovalFlow>("/product/approval-flows", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function simulateApprovalFlow(
  definition: Record<string, unknown>,
  receipt: Receipt,
): Promise<Record<string, unknown>> {
  return tenantRequest<Record<string, unknown>>("/product/approval-flows/simulate", {
    method: "POST",
    body: JSON.stringify({ definition, receipt }),
  });
}

export async function getInboundEmails(): Promise<{ items: InboundEmail[]; address: string }> {
  return tenantRequest<{ items: InboundEmail[]; address: string }>("/product/inbound-emails");
}

export async function receiveEmail(body: {
  sender: string;
  subject: string;
  attachments: Array<{ filename: string; content_type: string; size: number }>;
}): Promise<Record<string, unknown>> {
  return tenantRequest<Record<string, unknown>>("/product/inbound-emails", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function getRecurringExpenses(): Promise<{ items: RecurringExpense[] }> {
  return tenantRequest<{ items: RecurringExpense[] }>("/product/recurring-expenses");
}

export async function submitRecurringFeedback(body: {
  merchant: string;
  is_subscription: boolean;
}): Promise<Record<string, unknown>> {
  return tenantRequest<Record<string, unknown>>("/product/recurring-expenses/feedback", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Subscriptions (subscription intelligence layer)
// ---------------------------------------------------------------------------

export async function getSubscriptions(): Promise<SubscriptionListResponse> {
  return tenantRequest<SubscriptionListResponse>("/api/v1/subscriptions");
}

export async function getCancelGuide(
  subscriptionId: string,
): Promise<CancelGuide> {
  return tenantRequest<CancelGuide>(
    `/api/v1/subscriptions/${encodeURIComponent(subscriptionId)}/cancel-guide`,
  );
}

export async function setExchangeRate(body: {
  base: string;
  quote: string;
  rate: number;
  rate_date: string;
  source: string;
}): Promise<Record<string, unknown>> {
  return tenantRequest<Record<string, unknown>>("/product/exchange-rates", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function convertCurrency(body: {
  amount: number;
  base: string;
  quote: string;
  rate_date?: string;
}): Promise<{ converted: number; quote: string; rate: number }> {
  return tenantRequest<{ converted: number; quote: string; rate: number }>(
    "/product/currency/convert",
    { method: "POST", body: JSON.stringify(body) },
  );
}

export async function getPermissions(): Promise<PermissionMatrix> {
  return tenantRequest<PermissionMatrix>("/product/permissions");
}

export async function updatePermissions(body: {
  role: string;
  permissions: string[];
}): Promise<Record<string, unknown>> {
  return tenantRequest<Record<string, unknown>>("/product/permissions", {
    method: "PUT",
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Diagnostics
// ---------------------------------------------------------------------------

export async function getDiagnostics(): Promise<Diagnostics> {
  return tenantRequest<Diagnostics>("/product/diagnostics");
}

export async function downloadDiagnostics(): Promise<Blob> {
  return binaryRequest("/product/diagnostics/bundle");
}

// ---------------------------------------------------------------------------
// F1.3 household auth — magic-link login, invites, sessions
// ---------------------------------------------------------------------------

/** POST /auth/magic-link-request — request a magic link for an email. */
export async function requestMagicLink(body: {
  email: string;
  household_id?: string | null;
}): Promise<MagicLinkResponse> {
  return request<MagicLinkResponse>("/auth/magic-link-request", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

/** POST /auth/magic-link-verify — exchange a token for a session. */
export async function verifyMagicLink(token: string): Promise<SessionIdentity> {
  return request<SessionIdentity>("/auth/magic-link-verify", {
    method: "POST",
    body: JSON.stringify({ token }),
  });
}

/** POST /auth/session/me — resolve a session token. */
export async function resolveSession(sessionToken: string): Promise<SessionIdentity> {
  return request<SessionIdentity>("/auth/session/me", {
    method: "POST",
    body: JSON.stringify({ session_token: sessionToken }),
  });
}

/** POST /auth/households/{id}/invites — owner invites a member. */
export async function createInvite(
  householdId: string,
  body: { email: string; role: HouseholdRole },
): Promise<HouseholdInvite> {
  return tenantRequest<HouseholdInvite>(
    `/auth/households/${householdId}/invites`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

/** GET /auth/households/{id}/invites — list pending invites (owner only). */
export async function listInvites(householdId: string): Promise<{ items: HouseholdInvite[] }> {
  return tenantRequest<{ items: HouseholdInvite[] }>(
    `/auth/households/${householdId}/invites`,
  );
}

/** POST /auth/households/{id}/invites/{inviteId}/accept — accept + sign in. */
export async function acceptInvite(
  householdId: string,
  inviteId: string,
  token: string,
): Promise<SessionIdentity> {
  return request<SessionIdentity>(
    `/auth/households/${householdId}/invites/${inviteId}/accept`,
    { method: "POST", body: JSON.stringify({ token }) },
  );
}

// ---------------------------------------------------------------------------
// Google SSO + session lifecycle
// ---------------------------------------------------------------------------

/** GET /auth/google/status — whether Google SSO is enabled. */
export async function googleSsoEnabled(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/auth/google/status`);
    if (!res.ok) return false;
    const data = await res.json();
    return data.enabled === true;
  } catch {
    return false;
  }
}

/** POST /auth/session/logout — invalidate the current session. */
export async function logoutSession(): Promise<void> {
  const session = getSessionToken();
  await request("/auth/session/logout", {
    method: "POST",
    headers: session ? { Authorization: `Bearer ${session}` } : {},
  }).catch(() => {});
  clearSessionToken();
}

/** Alias — spec calls it `logout()` (POST /api/auth/session/logout Bearer-rel). */
export const logout = logoutSession;
