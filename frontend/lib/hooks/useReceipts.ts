"use client";

import useSWR from "swr";
import {
  searchReceipts,
  type SearchReceiptsParams,
} from "@/lib/api";
import type { PagedReceipts } from "@/lib/types";

export interface ReceiptListState {
  query?: string;
  status?: string;
  tag?: string;
  category?: string;
  minTotal?: number;
  maxTotal?: number;
  limit?: number;
  offset?: number;
  readiness?: string;
}

function toParams(state: ReceiptListState): SearchReceiptsParams {
  return {
    query: state.query || undefined,
    status: state.status || undefined,
    tag: state.tag || undefined,
    min_total: state.minTotal,
    max_total: state.maxTotal,
    limit: state.limit ?? 50,
    offset: state.offset ?? 0,
    readiness: state.readiness || undefined,
  };
}

export function useReceipts(state: ReceiptListState) {
  const key = `/product/receipts?${JSON.stringify(toParams(state))}`;
  const { data, error, isLoading, mutate } = useSWR<PagedReceipts>(key, () =>
    searchReceipts(toParams(state)),
  );
  return { data, error, isLoading, mutate };
}

export function useReceiptDetail(receiptId: string | undefined) {
  const { data, error, isLoading, mutate } = useSWR(
    receiptId ? `/receipts/${receiptId}` : null,
    () => searchReceipts({ query: "", limit: 200 }).then((page) => {
      const match = page.items.find((item) => item.receipt_id === receiptId);
      if (!match) throw new Error("Receipt not found");
      return match;
    }),
  );
  return { item: data, error, isLoading, mutate };
}
