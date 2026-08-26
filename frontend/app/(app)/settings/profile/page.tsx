"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { getPreferences, savePreferences } from "@/lib/api";
import type { Preferences } from "@/lib/types";
import { getLocale, setLocale, useTranslation, SUPPORTED_LOCALES, LOCALE_LABELS, type Locale } from "@/lib/i18n";

export default function ProfileSettingsPage() {
  const { t, locale } = useTranslation();
  const { data, error, isLoading, mutate } = useSWR<Preferences>("/product/preferences", getPreferences);
  const [compact, setCompact] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (data) {
      setCompact(data.compact);
      setHighContrast(data.high_contrast);
    }
  }, [data]);

  async function save() {
    setSaving(true);
    try {
      await savePreferences({ compact, high_contrast: highContrast });
      setSaved(true);
      mutate();
      window.setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  }

  async function changeLocale(next: Locale) {
    setLocale(next);
    try {
      await savePreferences({ language: next });
    } catch {
      // localStorage already reflects the new choice — backend is a nice-to-have sync
    }
    location.reload();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t("settings")}</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Settings · Profile</p>
      </div>

      <section className="card max-w-lg p-5">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Preferences</h2>
        {isLoading ? (
          <p className="mt-3 text-sm text-slate-400">Loading…</p>
        ) : error ? (
          <p className="mt-3 text-sm text-rose-600 dark:text-rose-400">Could not load preferences.</p>
        ) : (
          <div className="mt-4 space-y-4">
            <div>
              <label htmlFor="pref-language" className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
                Language
              </label>
              <select
                id="pref-language"
                className="input"
                value={locale}
                onChange={(event) => changeLocale(event.target.value as Locale)}
              >
                {SUPPORTED_LOCALES.map((loc) => (
                  <option key={loc} value={loc}>{LOCALE_LABELS[loc]}</option>
                ))}
              </select>
              <p className="mt-1 text-xs text-slate-400">
                {t("language")} — {t("selectLanguage")}.
              </p>
            </div>
            <label className="flex items-center justify-between gap-3 text-sm text-slate-700 dark:text-slate-200">
              <span>Compact mode</span>
              <input
                type="checkbox"
                checked={compact}
                onChange={(event) => setCompact(event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
            </label>
            <label className="flex items-center justify-between gap-3 text-sm text-slate-700 dark:text-slate-200">
              <span>High contrast</span>
              <input
                type="checkbox"
                checked={highContrast}
                onChange={(event) => setHighContrast(event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
            </label>
            <p className="text-xs text-slate-400">
              Onboarding: {data?.onboarding_done ? "complete ✓" : "not done yet"}
            </p>
            <button type="button" onClick={save} disabled={saving} className="btn-primary text-sm">
              {saving ? "Saving…" : "Save preferences"}
            </button>
            {saved ? (
              <span className="ml-2 text-sm text-emerald-600 dark:text-emerald-400" role="status">
                Saved ✓
              </span>
            ) : null}
          </div>
        )}
      </section>
    </div>
  );
}
