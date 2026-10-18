/** OCR scores are evidence, not a probability that a receipt is correct. */
export function averageConfidence(values: Record<string, unknown> | null | undefined): number | null {
  const scores = Object.values(values ?? {}).filter((value): value is number =>
    typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1);
  return scores.length ? scores.reduce((sum, value) => sum + value, 0) / scores.length : null;
}
