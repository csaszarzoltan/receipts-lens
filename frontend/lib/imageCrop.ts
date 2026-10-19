/**
 * Conservative automatic crop of a receipt photo to the bright paper area.
 * Axis-aligned only (no perspective correction). When the paper cannot be
 * separated from the background with confidence the image is left untouched,
 * so a wrong guess never removes receipt content.
 */
export interface CropBox { x: number; y: number; width: number; height: number; }

const ANALYSIS_SIDE = 320;
const MIN_CLASS_GAP = 60;      // paper and background must differ by this much (0-255)
const LINE_PAPER_SHARE = 0.2;  // a row/column counts when this share of it is paper
const MIN_AREA = 0.2;          // smaller than this is probably not the receipt
const MAX_AREA = 0.9;          // larger than this is not worth cropping
const MARGIN = 0.03;

function otsu(hist: number[], total: number): number {
  let sum = 0;
  for (let i = 0; i < 256; i++) sum += i * hist[i];
  let wB = 0, sumB = 0, best = 0, threshold = 127;
  for (let t = 0; t < 256; t++) {
    wB += hist[t];
    if (!wB) continue;
    const wF = total - wB;
    if (!wF) break;
    sumB += t * hist[t];
    const mB = sumB / wB, mF = (sum - sumB) / wF;
    const between = wB * wF * (mB - mF) * (mB - mF);
    if (between > best) { best = between; threshold = t; }
  }
  return threshold;
}

/** Bounding box (in the pixel grid of the input) of the paper area, or null. */
export function findReceiptBox(rgba: ArrayLike<number>, width: number, height: number): CropBox | null {
  if (width < 16 || height < 16 || rgba.length < width * height * 4) return null;
  const gray = new Uint8Array(width * height);
  const hist = new Array<number>(256).fill(0);
  for (let i = 0; i < gray.length; i++) {
    const g = Math.round(0.299 * rgba[i * 4] + 0.587 * rgba[i * 4 + 1] + 0.114 * rgba[i * 4 + 2]);
    gray[i] = g; hist[g]++;
  }
  const t = otsu(hist, gray.length);
  let nLow = 0, sLow = 0, nHigh = 0, sHigh = 0;
  for (let v = 0; v < 256; v++) {
    if (v <= t) { nLow += hist[v]; sLow += v * hist[v]; } else { nHigh += hist[v]; sHigh += v * hist[v]; }
  }
  if (!nLow || !nHigh || sHigh / nHigh - sLow / nLow < MIN_CLASS_GAP) return null;
  const rows = new Array<number>(height).fill(0), cols = new Array<number>(width).fill(0);
  for (let y = 0; y < height; y++) for (let x = 0; x < width; x++) if (gray[y * width + x] > t) { rows[y]++; cols[x]++; }
  const first = (a: number[], limit: number) => a.findIndex(v => v >= limit * LINE_PAPER_SHARE);
  const last = (a: number[], limit: number) => { for (let i = a.length - 1; i >= 0; i--) if (a[i] >= limit * LINE_PAPER_SHARE) return i; return -1; };
  const top = first(rows, width), bottom = last(rows, width), left = first(cols, height), right = last(cols, height);
  if (top < 0 || left < 0 || bottom <= top || right <= left) return null;
  const mx = Math.round((right - left) * MARGIN), my = Math.round((bottom - top) * MARGIN);
  const x0 = Math.max(0, left - mx), y0 = Math.max(0, top - my);
  const x1 = Math.min(width - 1, right + mx), y1 = Math.min(height - 1, bottom + my);
  const area = ((x1 - x0 + 1) * (y1 - y0 + 1)) / (width * height);
  if (area < MIN_AREA || area > MAX_AREA) return null;
  return { x: x0, y: y0, width: x1 - x0 + 1, height: y1 - y0 + 1 };
}

function scaleBox(box: CropBox, k: number, maxW: number, maxH: number): CropBox {
  const x = Math.max(0, Math.floor(box.x * k)), y = Math.max(0, Math.floor(box.y * k));
  return { x, y, width: Math.min(maxW - x, Math.ceil(box.width * k)), height: Math.min(maxH - y, Math.ceil(box.height * k)) };
}

function analyse(source: CanvasImageSource, width: number, height: number): { box: CropBox; k: number } | null {
  const k = Math.min(1, ANALYSIS_SIDE / Math.max(width, height));
  const w = Math.max(1, Math.round(width * k)), h = Math.max(1, Math.round(height * k));
  const canvas = document.createElement("canvas");
  canvas.width = w; canvas.height = h;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.drawImage(source, 0, 0, w, h);
  const box = findReceiptBox(ctx.getImageData(0, 0, w, h).data, w, h);
  return box ? { box, k: 1 / k } : null;
}

/** Crop box in the pixel grid of an already drawn canvas (camera capture), or null. */
export function receiptBoxFromCanvas(source: { width: number; height: number }): CropBox | null {
  try {
    const found = analyse(source as CanvasImageSource, source.width, source.height);
    return found ? scaleBox(found.box, found.k, source.width, source.height) : null;
  } catch { return null; }
}

/** Returns a cropped JPEG copy of a picked image, or the original file when no safe crop exists. */
export async function autoCropFile(file: File): Promise<File> {
  try {
    if (!file.type.startsWith("image/") || typeof createImageBitmap !== "function") return file;
    const bitmap = await createImageBitmap(file);
    try {
      const found = analyse(bitmap, bitmap.width, bitmap.height);
      if (!found) return file;
      const box = scaleBox(found.box, found.k, bitmap.width, bitmap.height);
      const out = document.createElement("canvas");
      out.width = box.width; out.height = box.height;
      const ctx = out.getContext("2d");
      if (!ctx) return file;
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, box.width, box.height);
      ctx.drawImage(bitmap, box.x, box.y, box.width, box.height, 0, 0, box.width, box.height);
      const blob = await new Promise<Blob | null>(resolve => out.toBlob(resolve, "image/jpeg", 0.92));
      if (!blob || blob.size === 0) return file;
      return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg", lastModified: file.lastModified });
    } finally { bitmap.close?.(); }
  } catch { return file; }
}
