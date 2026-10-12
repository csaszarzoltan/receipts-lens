"use client";

import React from "react";
import Link from "next/link";
import useSWR from "swr";
import { checkStatement, correctReceipt, getPreferences } from "@/lib/api";
import type { StatementLine, StatementReceipt, StatementResult } from "@/lib/types";
import { cx, effectiveBaseCurrency, formatDate, formatMoney } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";

type Money = (amount: number | null, currency?: string | null) => string;

function SectionCard({ title, desc, children }: { title: string; desc?: string; children: React.ReactNode }) {
  return (
    <section className="card p-5" aria-label={title}>
      <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
      {desc ? <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{desc}</p> : null}
      <div className="mt-3">{children}</div>
    </section>
  );
}

function LineRow({ line, money, extra }: { line: StatementLine; money: Money; extra?: React.ReactNode }) {
  return (
    <li className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 py-3">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{line.description || "—"}</p>
        <p className="text-xs text-slate-600 dark:text-slate-400">{formatDate(line.date)}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold tabular-nums text-slate-900 dark:text-slate-100">
          {money(line.amount, line.currency)}
        </span>
        {extra}
      </div>
    </li>
  );
}

export default function StatementPage() {
  const { t, locale } = useTranslation();
  const { data: prefs } = useSWR("/product/preferences", getPreferences);
  const baseCurrency = effectiveBaseCurrency(prefs, locale);
  const money: Money = (amount, currency) => formatMoney(amount, currency ?? baseCurrency);

  const [result, setResult] = React.useState<StatementResult | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [working, setWorking] = React.useState<string | null>(null);
  const [dragging, setDragging] = React.useState(false);
  const input = React.useRef<HTMLInputElement>(null);

  async function load(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await checkStatement(file));
    } catch (err) {
      setResult(null);
      setError(err instanceof Error && err.message ? `${t("statementError")} (${err.message})` : t("statementError"));
    } finally {
      setBusy(false);
    }
  }

  /** Saves the statement's amount on a receipt; the receipt then counts as matching. */
  async function confirm(receipt: StatementReceipt, amount: number) {
    setWorking(receipt.receipt_id);
    try {
      await correctReceipt(receipt.receipt_id, { changes: { total: amount }, action: "complete" }, receipt.version);
      setResult((current) => {
        if (!current) return current;
        const matched = current.matched.map((m) =>
          m.receipt.receipt_id === receipt.receipt_id ? { ...m, confirmed: true, receipt: { ...m.receipt, confirmed: true } } : m);
        const fromSuggestion = current.suggestions.find((s) => s.receipt.receipt_id === receipt.receipt_id);
        return {
          ...current,
          matched: fromSuggestion
            ? [...matched, { line: fromSuggestion.line, confirmed: true, receipt: { ...receipt, amount, confirmed: true } }]
            : matched,
          suggestions: current.suggestions.filter((s) => s.receipt.receipt_id !== receipt.receipt_id),
        };
      });
    } catch {
      setError(t("statementError"));
    } finally {
      setWorking(null);
    }
  }

  async function confirmAll(items: StatementResult["matched"]) {
    for (const m of items) await confirm(m.receipt, m.line.amount);
  }

  const total = result?.counts.lines ?? 0;
  const covered = result?.matched.length ?? 0;
  const pending = result?.matched.filter((m) => !m.confirmed) ?? [];
  const settled = result?.matched.filter((m) => m.confirmed) ?? [];

  return (
    <div className="space-y-6" data-testid="statement-page">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("statementTitle")}</h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-600 dark:text-slate-400">{t("statementDesc")}</p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); void load(e.dataTransfer.files?.[0]); }}
        className={cx(
          result ? "flex flex-col items-center gap-2 rounded-xl border-2 border-dashed px-6 py-4 text-center transition-colors" : "flex flex-col items-center gap-3 rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors",
          dragging
            ? "border-brand-500 bg-brand-50 dark:bg-brand-950"
            : "border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-900",
        )}
      >
        <span className="text-3xl" aria-hidden="true">🏦</span>
        <div className="flex flex-wrap items-center justify-center gap-2">
          <button type="button" className="btn-primary text-sm" disabled={busy} onClick={() => input.current?.click()}>
            {result ? t("statementAnother") : t("statementChoose")}
          </button>
          <span className="text-sm text-slate-600 dark:text-slate-400">{t("statementDrop")}</span>
        </div>
        <input
          ref={input}
          type="file"
          accept=".csv,.txt,text/csv"
          className="sr-only"
          aria-label={t("statementChoose")}
          data-testid="statement-file"
          onChange={(e) => { void load(e.target.files?.[0]); e.target.value = ""; }}
        />
        <p className="text-xs text-slate-600 dark:text-slate-400">{t("statementPrivacy")}</p>
        <p role="status" className="min-h-5 text-sm text-slate-700 dark:text-slate-300">{busy ? t("statementReading") : ""}</p>
      </div>

      {error ? (
        <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          {error}
        </p>
      ) : null}

      {result ? (
        <div className="space-y-6" data-testid="statement-result">
          <section className="card p-5" aria-label={t("statementCoverage")}>
            <div className="flex flex-wrap items-end justify-between gap-3">
              <p className="text-3xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
                {covered}
                <span className="text-lg font-semibold text-slate-600 dark:text-slate-400"> / {total}</span>{" "}
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{t("statementCoverage")}</span>
              </p>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {t("statementPeriod")}: {formatDate(result.period.from)} – {formatDate(result.period.to)}
              </p>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700" aria-hidden="true">
              <div className="h-full rounded-full bg-emerald-600 dark:bg-emerald-400"
                   style={{ width: `${total ? (covered / total) * 100 : 0}%` }} />
            </div>
            {result.counts.unmatched_receipts > 0 ? (
              <p className="mt-3 text-sm text-slate-700 dark:text-slate-300">
                <strong className="tabular-nums">{result.counts.unmatched_receipts}</strong> {t("statementUnmatchedReceipts")}
              </p>
            ) : null}
            <p className="mt-3 text-xs text-slate-600 dark:text-slate-400">
              {t("statementAssumed")}:{" "}
              {result.assumptions.direction === "negative_is_spending" ? t("statementDirNegative") : t("statementDirPositive")};{" "}
              {t("statementDayFirst")}.
              {result.assumptions.skipped_rows > 0 ? ` ${result.assumptions.skipped_rows} ${t("statementSkipped")}.` : ""}
            </p>
          </section>

          {result.suggestions.length > 0 ? (
            <SectionCard title={t("statementSuggestTitle")} desc={t("statementSuggestDesc")}>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {result.suggestions.map((s) => (
                  <li key={s.receipt.receipt_id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                    <div className="min-w-0 text-sm">
                      <p className="font-medium text-slate-900 dark:text-slate-100">{s.receipt.vendor || s.line.description || t("unknownVendorLabel")}</p>
                      <p className="text-slate-700 dark:text-slate-300">
                        {t("statementReceiptSays")}: <strong className="tabular-nums">{money(s.receipt.amount, s.receipt.currency)}</strong>
                        {" · "}
                        {t("statementBankSays")}: <strong className="tabular-nums">{money(s.line.amount, s.line.currency)}</strong>
                      </p>
                      <Link href={`/receipts/${s.receipt.receipt_id}`} className="text-xs font-medium text-brand-700 underline dark:text-brand-300">
                        {formatDate(s.receipt.date)}
                      </Link>
                    </div>
                    <button type="button" className="btn-secondary text-sm" disabled={working === s.receipt.receipt_id}
                            onClick={() => confirm(s.receipt, s.line.amount)}>
                      {t("statementUseAmount")}
                    </button>
                  </li>
                ))}
              </ul>
            </SectionCard>
          ) : null}

          {pending.length > 0 ? (
            <SectionCard title={t("statementConfirmTitle")} desc={t("statementConfirmDesc")}>
              <div className="mb-2">
                <button type="button" className="btn-primary text-sm" disabled={working !== null} onClick={() => confirmAll(pending)}>
                  {t("statementConfirmAll")} ({pending.length})
                </button>
              </div>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {pending.map((m) => (
                  <LineRow key={m.receipt.receipt_id} line={m.line} money={money}
                    extra={
                      <button type="button" className="btn-secondary text-sm" disabled={working === m.receipt.receipt_id}
                              onClick={() => confirm(m.receipt, m.line.amount)}>
                        {t("statementConfirm")}
                      </button>
                    } />
                ))}
              </ul>
            </SectionCard>
          ) : null}

          {result.unmatched_lines.length > 0 ? (
            <SectionCard title={t("statementNoReceiptTitle")} desc={t("statementNoReceiptDesc")}>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {result.unmatched_lines.map((line) => <LineRow key={line.row} line={line} money={money} />)}
              </ul>
              <Link href="/upload" className="btn-secondary mt-3 text-sm">{t("statementAddReceipt")}</Link>
            </SectionCard>
          ) : null}

          {result.unmatched_receipts.length > 0 ? (
            <SectionCard title={t("statementNotOnStatementTitle")} desc={t("statementNotOnStatementDesc")}>
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {result.unmatched_receipts.map((r) => (
                  <li key={r.receipt_id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                    <div className="min-w-0">
                      <Link href={`/receipts/${r.receipt_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:underline dark:text-slate-100">
                        {r.vendor || t("unknownVendorLabel")}
                      </Link>
                      <p className="text-xs text-slate-600 dark:text-slate-400">{formatDate(r.date)}</p>
                    </div>
                    <span className="text-sm font-semibold tabular-nums text-slate-900 dark:text-slate-100">{money(r.amount, r.currency)}</span>
                  </li>
                ))}
              </ul>
            </SectionCard>
          ) : null}

          {settled.length > 0 ? (
            <details className="card p-5">
              <summary className="cursor-pointer text-base font-semibold text-slate-900 dark:text-slate-100">
                {t("statementMatchedTitle")} ({settled.length})
              </summary>
              <ul className="mt-2 divide-y divide-slate-100 dark:divide-slate-800">
                {settled.map((m) => <LineRow key={m.receipt.receipt_id} line={m.line} money={money} />)}
              </ul>
            </details>
          ) : null}

          {result.counts.unmatched_lines === 0 && result.counts.suggestions === 0 && pending.length === 0 ? (
            <p role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200">
              {t("statementAllGood")}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
