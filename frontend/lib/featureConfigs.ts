/** One config per v2 feature page. FeatureWorkbench renders every page from these. */

export type FeatureFieldType = "text" | "number" | "date" | "money";

export type FeatureField = {
  /** Payload key; also the i18n key suffix (field.<name>). */
  name: string;
  type?: FeatureFieldType;
  required?: boolean;
};

export type FeatureConfig = {
  /** Prefix for data-testid values, e.g. "reconciliation" -> reconciliation-page. */
  testId: string;
  /** i18n key suffix: f.<key>.title / .description / .create. */
  key: string;
  /** Backend collection path, e.g. /api/v2/refunds. */
  path: string;
  /** Create-form fields. The item name (client_reference) is always the first field. */
  fields: FeatureField[];
};

const NAME: FeatureField = { name: "client_reference", required: true };

export const FEATURE_CONFIGS = {
  reconciliation: {
    testId: "reconciliation",
    key: "reconciliation",
    path: "/api/v2/reconciliation/matches",
    fields: [
      NAME,
      { name: "bank_reference" },
      { name: "card_reference" },
      { name: "amount", type: "money" },
      { name: "currency" },
    ],
  },
  missing_receipts: {
    testId: "missing_receipts",
    key: "missing_receipts",
    path: "/api/v2/missing-receipts",
    fields: [NAME, { name: "merchant", required: true }, { name: "amount", type: "money", required: true }, { name: "date", type: "date" }],
  },
  refunds: {
    testId: "refunds",
    key: "refunds",
    path: "/api/v2/refunds",
    fields: [NAME, { name: "merchant", required: true }, { name: "amount", type: "money", required: true }, { name: "original_receipt" }],
  },
  cost_splits: {
    testId: "cost_splits",
    key: "cost_splits",
    path: "/api/v2/cost-splits",
    fields: [NAME, { name: "receipt" }, { name: "total", type: "money", required: true }, { name: "participants", required: true }, { name: "currency" }],
  },
  savings_goals: {
    testId: "savings_goals",
    key: "savings_goals",
    path: "/api/v2/savings-goals",
    fields: [NAME, { name: "target_amount", type: "money", required: true }, { name: "currency", required: true }, { name: "deadline", type: "date" }, { name: "saved_amount", type: "money" }],
  },
  price_tracking: {
    testId: "price_tracking",
    key: "price_tracking",
    path: "/api/v2/price-tracking",
    fields: [NAME, { name: "product", required: true }, { name: "merchant" }, { name: "watch_price", type: "money", required: true }],
  },
  data_quality: {
    testId: "data_quality",
    key: "data_quality",
    path: "/api/v2/quality-tasks",
    fields: [NAME, { name: "issue_type", required: true }, { name: "receipt" }, { name: "period" }],
  },
  period_close: {
    testId: "period_close",
    key: "period_close",
    path: "/api/v2/accounting-periods",
    fields: [NAME, { name: "period", required: true }, { name: "note" }],
  },
  offline_sync: {
    testId: "offline_sync",
    key: "offline_sync",
    path: "/api/v2/offline-sync",
    fields: [NAME, { name: "device", required: true }, { name: "receipt" }],
  },
  mobile_receipts: {
    testId: "mobile_receipts",
    key: "mobile_receipts",
    path: "/api/v2/mobile-receipts",
    fields: [NAME, { name: "merchant" }, { name: "amount", type: "money" }],
  },
} satisfies Record<string, FeatureConfig>;
