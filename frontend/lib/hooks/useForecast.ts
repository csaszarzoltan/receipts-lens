"use client";

import useSWR from "swr";
import {
  getAnomalies,
  getBudgetVariance,
  getForecast,
  type ForecastParams,
} from "@/lib/api";
import type {
  AnomalyResult,
  BudgetVarianceResult,
  ForecastResult,
} from "@/lib/types";

export function useForecast(params: ForecastParams = {}) {
  const key = `/forecasts?${JSON.stringify(params)}`;
  const forecast = useSWR<ForecastResult>(key, () => getForecast(params));
  return { data: forecast.data, error: forecast.error, isLoading: forecast.isLoading };
}

export function useAnomalies(period = "monthly") {
  const key = `/forecasts/anomalies?${period}`;
  const anomalies = useSWR<AnomalyResult>(key, () =>
    getAnomalies({ period, method: "zscore", threshold: 2.0 }),
  );
  return {
    data: anomalies.data,
    error: anomalies.error,
    isLoading: anomalies.isLoading,
  };
}

export function useBudgetVariance(horizon = 1) {
  const key = `/forecasts/budget-variance?horizon=${horizon}`;
  const variance = useSWR<BudgetVarianceResult>(key, () =>
    getBudgetVariance({ horizon }),
  );
  return {
    data: variance.data,
    error: variance.error,
    isLoading: variance.isLoading,
  };
}
