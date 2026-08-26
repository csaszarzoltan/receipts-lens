/**
 * Frontend feature flags (build-time constants).
 *
 * Flags are read from NEXT_PUBLIC_* env vars at build time and written as
 * plain comparisons against string literals (no helper calls), so the
 * bundler can fold them to `true`/`false` and tree-shake the disabled
 * branches out of the production bundle entirely.
 *
 * AI Scan (LLM vision OCR) is a FUTURE PAID FEATURE (see
 * docs/plans/production-rollout-2026-08-13.md v3, "Végjegyzet — AI-scan").
 * The production rollout deliberately ships WITHOUT any vision-LLM API key,
 * so the flag defaults to OFF everywhere:
 *
 *   - unset  → disabled (safe default; prod builds must not call vision API)
 *   - "1" | "true" | "yes" | "on" (exact, lowercase) → enabled (dev/demo)
 *   - anything else → disabled
 *
 * When disabled, the upload page hides the AiScanToggle and renders an
 * upgrade prompt instead, and useUpload() hard-routes any AI-mode request
 * to the classic Tesseract pipeline as defence-in-depth.
 */

/** Raw build-time value of NEXT_PUBLIC_AI_SCAN_ENABLED. */
const AI_SCAN_RAW = process.env.NEXT_PUBLIC_AI_SCAN_ENABLED;

/**
 * AI Scan availability flag. Default OFF — enable explicitly with
 * NEXT_PUBLIC_AI_SCAN_ENABLED=1 at build time (dev/demo environments).
 */
export const AI_SCAN_ENABLED =
  AI_SCAN_RAW === "1" ||
  AI_SCAN_RAW === "true" ||
  AI_SCAN_RAW === "yes" ||
  AI_SCAN_RAW === "on";
