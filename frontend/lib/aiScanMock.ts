/**
 * Dev-only mock for the AI-mode OCR upload (lib/api.ts → uploadReceiptWithAi).
 *
 * The backend `ai_scan` endpoint lands in a sibling task (t_bc0540eb); until
 * then the UI is developed and demoed against this mock, which follows the
 * exact API contract from the acceptance criteria:
 *
 *   response.source           — "vision" | "tesseract"
 *   response.ai_result        — vision-pipeline extraction (AI mode only)
 *   response.tesseract_result — Tesseract-pipeline extraction (AI mode only)
 *
 * Enable it for local development / visual verification with:
 *
 *   NEXT_PUBLIC_USE_MOCK_AI=1 npm run dev
 *
 * When the flag is unset the UI calls the real backend endpoint and surfaces
 * real errors — the mock never silently replaces a live API failure.
 */
import type { AiExtraction, AiScanUploadResponse, OcrSource } from "./types";

/** Realistic vision-pipeline extraction (mock). */
export const MOCK_VISION_EXTRACTION: AiExtraction = {
  merchant: "Café Central Zürich",
  date: "2026-08-05",
  total: 24.5,
  tax: 1.95,
  currency: "CHF",
  line_items: [
    { name: "Flat white", price: 5.5, quantity: 2, amount: 11.0 },
    { name: "Avocado toast", price: 12.5, quantity: 1, amount: 12.5 },
  ],
  confidence: { merchant: 0.97, date: 0.92, total: 0.99, tax: 0.88, line_items: 0.95 },
};

/** Realistic Tesseract-pipeline extraction (mock) — lower fidelity, same shape. */
export const MOCK_TESSERACT_EXTRACTION: AiExtraction = {
  merchant: "Cafe Central Z?rich",
  date: "2026-08-05",
  total: 24.5,
  tax: 1.95,
  currency: "CHF",
  line_items: [
    { name: "Flat white", price: 5.5, quantity: 2, amount: 11.0 },
    { name: "Avocado toast", price: 12.5, quantity: 1, amount: 12.5 },
  ],
  confidence: { merchant: 0.74, date: 0.91, total: 0.81, tax: 0.62, line_items: 0.66 },
};

/** Mock for the fallback path (vision unavailable → Tesseract used). */
export const MOCK_TESSERACT_FALLBACK_RESPONSE: AiScanUploadResponse = {
  receipt_id: "mock-receipt-0002",
  source: "tesseract",
  receipt: {
    vendor: "Cafe Central Z?rich",
    total: 24.5,
    date: "2026-08-05",
    tax: 1.95,
    currency: "CHF",
    line_items: MOCK_TESSERACT_EXTRACTION.line_items,
    confidence: MOCK_TESSERACT_EXTRACTION.confidence,
  },
  metadata: null,
  status: "completed",
  version: 1,
  readiness: { state: "exportable", issues: [] },
  created_at: new Date().toISOString(),
  ai_result: MOCK_TESSERACT_EXTRACTION,
  tesseract_result: MOCK_TESSERACT_EXTRACTION,
};

/**
 * Build a full AI-mode mock response for a given source. When the source is
 * "tesseract" (fallback), the panel shows the friendly fallback notice.
 */
export function mockAiScanResponse(source: OcrSource = "vision"): AiScanUploadResponse {
  const ai = source === "vision" ? MOCK_VISION_EXTRACTION : MOCK_TESSERACT_EXTRACTION;
  const tesseract = MOCK_TESSERACT_EXTRACTION;
  return {
    receipt_id: source === "vision" ? "mock-receipt-0001" : "mock-receipt-0002",
    source,
    receipt: {
      vendor: ai.merchant ?? "Unknown vendor",
      total: ai.total,
      date: ai.date,
      tax: ai.tax,
      currency: ai.currency,
      line_items: ai.line_items,
      confidence: ai.confidence,
    },
    metadata: null,
    status: "completed",
    version: 1,
    readiness: { state: "exportable", issues: [] },
    created_at: new Date().toISOString(),
    ai_result: ai,
    tesseract_result: tesseract,
  };
}

/** True only when the dev mock is explicitly enabled via env var. */
export const AI_MOCK_ENABLED =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_USE_MOCK_AI === "1";

/**
 * Pick a mock response for a given file name. Files hinting at poor quality
 * ("blurry", "ocr", "fallback", "handwritten") resolve to the Tesseract
 * fallback so the fallback notice can be demoed; everything else resolves to
 * the full vision result.
 */
export function mockAiScanResponseForFile(fileName: string): AiScanUploadResponse {
  const name = fileName.toLowerCase();
  const fallback = ["blur", "ocr", "fallback", "handwritten", "dark"].some((hint) =>
    name.includes(hint),
  );
  return mockAiScanResponse(fallback ? "tesseract" : "vision");
}
