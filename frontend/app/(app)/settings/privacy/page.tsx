"use client";

import { useState } from "react";
import { purgeExpired, setRetention } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";

export default function PrivacySettingsPage() {
  const { t } = useTranslation();
  const [days, setDays] = useState("365");
  const [retentionSaved, setRetentionSaved] = useState(false);
  const [purgeResult, setPurgeResult] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function saveRetention() {
    setBusy(true);
    try {
      const result = await setRetention(Number(days) || 365);
      setRetentionSaved(true);
      window.setTimeout(() => setRetentionSaved(false), 2000);
    } finally {
      setBusy(false);
    }
  }

  async function purge() {
    setBusy(true);
    try {
      const result = await purgeExpired();
      setPurgeResult(`${t("purgedPrefix")}${result.purged}${t("purgedSuffix")}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("privacy")}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("retentionSubtitle")}
        </p>
      </div>

      <section className="card max-w-lg p-5">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("retentionPolicy")}</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("retentionHint")}
        </p>
        <div className="mt-4 flex gap-3">
          <input
            type="number"
            min="30"
            className="input w-32"
            value={days}
            onChange={(event) => setDays(event.target.value)}
            aria-label="Retention days"
          />
          <button type="button" onClick={saveRetention} disabled={busy} className="btn-primary text-sm">
            Save
          </button>
          {retentionSaved ? (
            <span className="self-center text-sm text-emerald-600 dark:text-emerald-400" role="status">{t("saved")}</span>
          ) : null}
        </div>
      </section>

      <section className="card max-w-lg p-5">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">{t("purgeExpiredData")}</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("purgeHint")}
        </p>
        <button type="button" onClick={purge} disabled={busy} className="btn-secondary mt-4 text-sm">
          {busy ? t("working") : t("purgeButton")}
        </button>
        {purgeResult ? (
          <p className="mt-3 text-sm text-emerald-600 dark:text-emerald-400" role="status">{purgeResult}</p>
        ) : null}
      </section>
    </div>
  );
}
