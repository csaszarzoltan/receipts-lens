"use client";

import useSWR from "swr";
import { getDashboard, getWorkQueue } from "@/lib/api";
import type { DashboardData, WorkQueueItem } from "@/lib/types";

export function useDashboard() {
  const dashboard = useSWR<DashboardData>("/product/dashboard", getDashboard);
  const queue = useSWR<{ items: WorkQueueItem[] }>("/product/work-queue", () =>
    getWorkQueue(8),
  );
  return {
    data: dashboard.data,
    error: dashboard.error,
    isLoading: dashboard.isLoading,
    queue: queue.data?.items ?? [],
    queueError: queue.error,
  };
}
