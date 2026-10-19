/**
 * Client-side photo quality check run before a receipt is uploaded.
 * Blur: variance of the 4-neighbour Laplacian of the grey image, measured on
 * a copy scaled to MAX_SIDE so the score does not depend on camera resolution.
 * Dark: mean luma. Any failure to measure counts as "ok": the check must never
 * block an upload by itself.
 */
export type QualityIssue = "blurry" | "dark";
export interface QualityResult { ok: boolean; reason?: QualityIssue; sharpness?: number; brightness?: number; }

export const MAX_SIDE = 640;
export const BLUR_VARIANCE_MIN = 40;
export const DARK_MEAN_MIN = 55;

/** Score an RGBA pixel buffer (as returned by canvas getImageData). */
export function assessPixels(rgba: ArrayLike<number>, width: number, height: number): QualityResult {
  if (width < 3 || height < 3 || rgba.length < width * height * 4) return { ok: true };
  const gray = new Float32Array(width * height);
  let sum = 0;
  for (let i = 0; i < gray.length; i++) {
    const g = 0.299 * rgba[i * 4] + 0.587 * rgba[i * 4 + 1] + 0.114 * rgba[i * 4 + 2];
    gray[i] = g;
    sum += g;
  }
  const brightness = sum / gray.length;
  let lapSum = 0, lapSq = 0, n = 0;
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const i = y * width + x;
      const lap = 4 * gray[i] - gray[i - 1] - gray[i + 1] - gray[i - width] - gray[i + width];
      lapSum += lap; lapSq += lap * lap; n++;
    }
  }
  const mean = lapSum / n;
  const sharpness = lapSq / n - mean * mean;
  if (brightness < DARK_MEAN_MIN) return { ok: false, reason: "dark", sharpness, brightness };
  if (sharpness < BLUR_VARIANCE_MIN) return { ok: false, reason: "blurry", sharpness, brightness };
  return { ok: true, sharpness, brightness };
}

function scaled(width: number, height: number): { w: number; h: number } {
  const k = Math.min(1, MAX_SIDE / Math.max(width, height));
  return { w: Math.max(1, Math.round(width * k)), h: Math.max(1, Math.round(height * k)) };
}

/** Synchronous check of an already drawn canvas (camera capture). */
export function assessCanvas(source: { width: number; height: number }): QualityResult {
  try {
    const { w, h } = scaled(source.width, source.height);
    const small = document.createElement("canvas");
    small.width = w; small.height = h;
    const ctx = small.getContext("2d");
    if (!ctx) return { ok: true };
    ctx.drawImage(source as CanvasImageSource, 0, 0, w, h);
    return assessPixels(ctx.getImageData(0, 0, w, h).data, w, h);
  } catch { return { ok: true }; }
}

/** Check a chosen or dropped image file. */
export async function assessImageQuality(file: File): Promise<QualityResult> {
  try {
    if (!file.type.startsWith("image/") || typeof createImageBitmap !== "function") return { ok: true };
    const bitmap = await createImageBitmap(file);
    try {
      const { w, h } = scaled(bitmap.width, bitmap.height);
      const canvas = document.createElement("canvas");
      canvas.width = w; canvas.height = h;
      const ctx = canvas.getContext("2d");
      if (!ctx) return { ok: true };
      ctx.drawImage(bitmap, 0, 0, w, h);
      return assessPixels(ctx.getImageData(0, 0, w, h).data, w, h);
    } finally { bitmap.close?.(); }
  } catch { return { ok: true }; }
}
