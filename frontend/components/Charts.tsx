"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatMoney } from "@/lib/utils";

/**
 * Recharts-based charts shared by the dashboard, forecast and budget views.
 * All chart components are client-side (recharts requires the DOM).
 */

export interface SpendPoint {
  label: string;
  amount: number;
}

/** Simple bar/line spending chart (dashboard trend). */
export function SpendingChart({
  data,
  height = 260,
  currency = "USD",
}: {
  data: SpendPoint[];
  height?: number;
  currency?: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <YAxis tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <Tooltip
          cursor={{ fill: "currentColor", opacity: 0.06 }}
          formatter={(value) => [formatMoney(Number(value), currency), "Spend"]}
        />
        <Bar dataKey="amount" fill="var(--chart-primary, #1d5ef1)" radius={[6, 6, 0, 0]} maxBarSize={42} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export interface ForecastPoint {
  label: string;
  actual?: number;
  projected?: number;
  low?: number;
  high?: number;
}

/**
 * Forecast chart — next-period projection per category. Categories are not a
 * time axis, so they are drawn as bars (a line between them would suggest a trend).
 */
export function ForecastChart({
  data,
  height = 280,
  currency = "USD",
}: {
  data: ForecastPoint[];
  height?: number;
  currency?: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <YAxis tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <Tooltip
          cursor={{ fill: "currentColor", opacity: 0.06 }}
          formatter={(value) => formatMoney(Number(value), currency)}
        />
        <Bar dataKey="projected" name="Projected" fill="var(--chart-primary, #1d5ef1)" radius={[4, 4, 0, 0]} maxBarSize={42} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export interface VariancePoint {
  label: string;
  budgeted: number;
  projected: number;
  overage: number;
}

/** Budget variance chart — budgeted vs projected per category. */
export function VarianceChart({
  data,
  height = 280,
  currency = "USD",
}: {
  data: VariancePoint[];
  height?: number;
  currency?: string;
}) {
  const STATUS_COLORS = ["#1d5ef1", "#0f9d58", "#d97706", "#dc2626"];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <YAxis tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <Tooltip formatter={(value) => formatMoney(Number(value), currency)} />
        <Bar dataKey="budgeted" name="Budgeted" fill="#94a3b8" radius={[4, 4, 0, 0]} maxBarSize={28} />
        <Bar dataKey="projected" name="Projected" radius={[4, 4, 0, 0]} maxBarSize={28}>
          {data.map((point, index) => (
            <Cell key={point.label} fill={STATUS_COLORS[Math.min(index, STATUS_COLORS.length - 1)]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
