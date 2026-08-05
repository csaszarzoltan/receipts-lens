"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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
}: {
  data: SpendPoint[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <YAxis tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <Tooltip
          cursor={{ fill: "currentColor", opacity: 0.06 }}
          formatter={(value) => [`$${Number(value).toFixed(2)}`, "Spend"]}
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

/** Forecast chart — actuals (line) + projected band (area) per category. */
export function ForecastChart({ data, height = 280 }: { data: ForecastPoint[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <YAxis tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
        <Line type="monotone" dataKey="actual" name="Actual" stroke="#0f9d58" strokeWidth={2} dot={{ r: 3 }} />
        <Line type="monotone" dataKey="projected" name="Projected" stroke="#1d5ef1" strokeWidth={2} strokeDasharray="6 3" dot={{ r: 3 }} />
        <Line type="monotone" dataKey="low" name="Low" stroke="#1d5ef1" strokeWidth={0} dot={false} />
        <Line type="monotone" dataKey="high" name="High" stroke="#1d5ef1" strokeWidth={0} dot={false} />
      </LineChart>
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
export function VarianceChart({ data, height = 280 }: { data: VariancePoint[]; height?: number }) {
  const STATUS_COLORS = ["#1d5ef1", "#0f9d58", "#d97706", "#dc2626"];
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.12} />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <YAxis tick={{ fontSize: 12 }} stroke="currentColor" opacity={0.5} />
        <Tooltip formatter={(value) => `$${Number(value).toFixed(2)}`} />
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
