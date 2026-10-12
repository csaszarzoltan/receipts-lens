"use client";

import React from "react";
import Link from "next/link";
import { mutate } from "swr";
import { importEnyugta, type EnyugtaImportResult } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

/** Receipts from NAV's eNyugta buyer app arrive as data, so they need no reading and no confirming. */
export default function EnyugtaImport() {
  const { t, locale } = useTranslation();
  const [busy, setBusy] = React.useState(false);
  const [result, setResult] = React.useState<EnyugtaImportResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const input = React.useRef<HTMLInputElement>(null);
  if (locale !== "hu") return null;

  async function load(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await importEnyugta(file));
      void mutate((key) => typeof key === "string" && key.startsWith("/product/"));
    } catch (err) {
      setResult(null);
      setError(err instanceof Error && err.message ? `${t("enyugtaError")} (${err.message})` : t("enyugtaError"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card p-5" aria-label={t("enyugtaTitle")} data-testid="enyugta-import">
      <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("enyugtaTitle")}</h2>
      <p className="mt-1 max-w-2xl text-sm text-slate-600 dark:text-slate-400">{t("enyugtaDesc")}</p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <button type="button" className="btn-secondary text-sm" disabled={busy} onClick={() => input.current?.click()}>
          {busy ? t("enyugtaReading") : t("enyugtaChoose")}
        </button>
        <input
          ref={input}
          type="file"
          accept=".xml,text/xml,application/xml"
          className="sr-only"
          aria-label={t("enyugtaChoose")}
          data-testid="enyugta-file"
          onChange={(e) => { void load(e.target.files?.[0]); e.target.value = ""; }}
        />
        {result ? (
          <p role="status" className="text-sm text-slate-800 dark:text-slate-200">
            <strong className="tabular-nums">{result.imported}</strong> {t("enyugtaImported")} ·{" "}
            <span className="tabular-nums">{result.duplicates}</span> {t("enyugtaDuplicates")}
            {result.skipped.length > 0 ? <> · <span className="tabular-nums">{result.skipped.length}</span> {t("enyugtaSkipped")}</> : null}
            {" "}
            <Link href="/receipts" className="font-medium text-brand-700 underline dark:text-brand-300">{t("enyugtaView")}</Link>
          </p>
        ) : null}
        {error ? <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
      </div>
    </section>
  );
}
