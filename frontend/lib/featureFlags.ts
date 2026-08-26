/**
 * Frontend feature flags (build-time constants).
 *
 * Flags are read from NEXT_PUBLIC_* env vars at build time, so they are
 * inlined into the client bundle — changing them requires a rebuild.
 *
 * AI Scan (LLM vision OCR) is a FUTURE PAID FEATURE (see
 * docs/plans/production-rollout-2026-08-13.md v3, "Végjegyzet — AI-scan").
 * The production rollout deliberately ships WITHOUT any vision-LLM API key,
 * so the flag defaults to OFF everywhere:
 *
 *   - unset  → disabled (safe default; prod builds must not call vision API)
 *   - "1"/"true"/"yes"/"on" (case-insensitive) → enabled (local dev/demo)
 *   - anything else → disabled
 *
 * When disabled, the upload page hides the AiScanToggle and renders an
 * upgrade prompt instead, and useUpload() hard-routes any AI-mode request
 * to the classic Tesseract pipeline as defence-in-depth.
 */
function parseFlag(value: string | undefined): boolean {
  if (value === undefined || value === "") return false;
  const normalized = value.trim().toLowerCase();
  return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on";
}

/**
 * AI Scan availability flag. Default OFF — enable explicitly with
 * NEXT_PUBLIC_AI_SCAN_ENABLED=1 at build time (dev/demo environments).
 */
export const AI_SCAN_ENABLED = parseFlag(process.env.NEXT_PUBLIC_AI_SCAN_ENABLED);
