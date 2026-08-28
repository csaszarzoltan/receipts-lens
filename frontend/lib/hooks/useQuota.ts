import { useCallback, useState } from "react";
import useSWR from "swr";
import { tenantRequest } from "@/lib/api";

export interface QuotaState {
  used: number;
  limit: number | null;
  remaining: number | null;
  allowed: boolean;
  period: string;
  pro: boolean;
}

export function useQuota() {
  const { data, error, isLoading, mutate } = useSWR<QuotaState>("/api/v1/quota", (path: string) =>
    tenantRequest<QuotaState>(path),
  );
  return { quota: data ?? null, error, isLoading, mutate };
}

export function useQuotaRefresh() {
  const [refreshing, setRefreshing] = useState(false);
  const refresh = useCallback(async (mutate: () => Promise<unknown>) => {
    setRefreshing(true);
    try {
      await mutate();
    } finally {
      setRefreshing(false);
    }
  }, []);
  return { refreshing, refresh };
}
