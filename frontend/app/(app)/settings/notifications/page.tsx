"use client";

import Link from "next/link";
import { useState } from "react";
import useSWR from "swr";
import { getPreferences, savePreferences } from "@/lib/api";
import { useTranslation } from "@/lib/i18n";
import { PageSkeleton } from "@/components/Skeleton";
import type { Preferences } from "@/lib/types";

export default function NotificationSettingsPage() {
  const { t } = useTranslation();
  const { data, error, mutate } = useSWR("/product/preferences", getPreferences);
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">("idle");

  async function save(value: Preferences["insight_frequency"]) {
    setState("saving");
    try {
      await savePreferences({ insight_frequency: value });
      await mutate();
      setState("saved");
    } catch {
      setState("error");
    }
  }

  if (error) return <p role="alert">{t("couldNotLoad")}</p>;
  if (!data) return <PageSkeleton />;

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">{t("notificationSettings")}</h1>
      <section className="card p-5">
        <label htmlFor="insight-frequency" className="block font-medium">
          {t("notificationFrequency")}
        </label>
        <p className="my-3 text-sm text-slate-600 dark:text-slate-400">{t("insightCadenceHint")}</p>
        <select
          id="insight-frequency"
          className="input max-w-sm"
          disabled={state === "saving"}
          value={data.insight_frequency ?? ""}
          onChange={e => save(e.target.value as Preferences["insight_frequency"])}
        >
          <option value="" disabled>{t("chooseSummaryCadence")}</option>
          {(["daily", "weekly", "never"] as const).map(value => (
            <option key={value} value={value}>{t(value)}</option>
          ))}
        </select>
        <p role={state === "error" ? "alert" : "status"} className="mt-3 text-sm">
          {state === "saving" ? t("savingLabel") : state === "error" ? t("saveFailed") : state === "saved" ? t("metadataSaved") : ""}
        </p>
      </section>
      <div className="flex flex-wrap gap-3">
        <Link href="/subscriptions" className="btn-secondary">{t("emailNotifications")} · {t("subscriptions")}</Link>
        <Link href="/insights" className="btn-secondary">{t("insights")}</Link>
      </div>
    </div>
  );
}
