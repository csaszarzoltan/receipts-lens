import type { ReviewItem } from "@/lib/types";

/** True when the line items were read and their sum differs from the receipt total. */
export function hasLineMismatch(item: ReviewItem): boolean {
  return item.checks?.lines_match === false;
}

/** Review queue order: receipts whose lines do not add up first, otherwise unchanged. */
export function sortReviewItems(items: ReviewItem[]): ReviewItem[] {
  return items
    .map((item, index) => ({ item, index }))
    .sort((a, b) => Number(hasLineMismatch(b.item)) - Number(hasLineMismatch(a.item)) || a.index - b.index)
    .map(entry => entry.item);
}
