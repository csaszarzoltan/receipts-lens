"use client";

import { useRef, useState, type FormEvent, type ReactNode } from "react";
import useSWR from "swr";
import EmptyState from "@/components/EmptyState";
import Pill from "@/components/Pill";
import { SkeletonCard } from "@/components/Skeleton";
import type { FeatureConfig, FeatureField } from "@/lib/featureConfigs";
import {
  commandFeatureItem,
  createFeatureItem,
  FeatureApiError,
  listFeatureItems,
  newIdempotencyKey,
  type FeatureAction,
  type FeatureItem,
} from "@/lib/featureApi";
import { featureStatusTone } from "@/lib/featureStatus";
import { ft } from "@/lib/featureI18n";
import { formatDate, formatMoney } from "@/lib/utils";
import { useBaseCurrency } from "@/lib/featureCurrency";
import { useTranslation } from "@/lib/i18n";

type Shares = Array<{ name: string; amount: number }>;

/** Statuses that need a sentence of explanation under the pill. */
const STATUS_HINTS = ["CONFLICT", "FAILED", "NEEDS_REVIEW", "BLOCKED", "AT_RISK"];

function errorText(err: unknown, locale: string): string {
  if (err instanceof FeatureApiError) return err.message;
  return err instanceof Error ? err.message : ft("ui.unknownError", locale);
}

/** Parse a form value for the wire: numbers stay numbers, blanks are dropped. */
function toWire(value: string, type: string | undefined): string | number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (type === "number" || type === "money") return Number(trimmed);
  return trimmed;
}

function displayValue(field: FeatureField, raw: unknown, currency: string, locale: string): string {
  if (raw === null || raw === undefined || raw === "") return "";
  if (field.type === "money") return formatMoney(Number(raw), currency);
  if (field.type === "date") return formatDate(String(raw), locale);
  return String(raw);
}

function InputField({
  id,
  label,
  type,
  value,
  required,
  onChange,
}: {
  id: string;
  label: string;
  type: "text" | "number" | "date";
  value: string;
  required?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label htmlFor={id} className="block text-sm font-medium text-slate-700 dark:text-slate-200">
      {label}
      <input
        id={id}
        className="input mt-1"
        type={type}
        step={type === "number" ? "any" : undefined}
        value={value}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

/**
 * Shared workbench for the v2 feature pages: list, create, and the actions the server
 * allows for each item. Double clicks cannot duplicate work: the create form and every
 * action are guarded, and the create form keeps its Idempotency-Key until a save succeeds.
 */
export default function FeatureWorkbench({ config, header }: { config: FeatureConfig; header?: ReactNode }) {
  const { locale } = useTranslation();
  const baseCurrency = useBaseCurrency();
  const { data, error, isLoading, mutate } = useSWR(config.path, () => listFeatureItems(config.path));
  const [adding, setAdding] = useState(false);
  const [values, setValues] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const submitting = useRef(false);
  const formKey = useRef(newIdempotencyKey());
  const [pending, setPending] = useState<{ itemId: string; action: FeatureAction } | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [inputError, setInputError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const busyRef = useRef<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const items: FeatureItem[] = data ?? [];
  const nameField = config.fields[0];
  const fields = config.fields.slice(1);
  const t = (key: string, params?: Record<string, string | number>) => ft(key, locale, params);
  // A currency field shows the household's currency until someone types another one.
  const valueOf = (name: string) => values[name] ?? (name === "currency" ? baseCurrency : "");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (submitting.current) return;
    const name = (values[nameField.name] ?? "").trim();
    if (!name) {
      setFormError(t("ui.nameRequired"));
      return;
    }
    const payload: Record<string, unknown> = {};
    for (const field of fields) {
      const wire = toWire(valueOf(field.name), field.type);
      if (wire === null) {
        if (field.required) {
          setFormError(t("ui.required", { field: t(`field.${field.name}`) }));
          return;
        }
        continue;
      }
      if (typeof wire === "number" && !Number.isFinite(wire)) {
        setFormError(t("ui.invalidNumber", { field: t(`field.${field.name}`) }));
        return;
      }
      payload[field.name] = field.name === "currency" && typeof wire === "string" ? wire.toUpperCase() : wire;
    }
    submitting.current = true;
    setSaving(true);
    setFormError(null);
    try {
      await createFeatureItem(config.path, { client_reference: name, payload }, formKey.current);
      setValues({});
      formKey.current = newIdempotencyKey();
      setAdding(false);
      await mutate();
    } catch (err) {
      // Keep the key: a retry after a failed request must not create a second item.
      setFormError(errorText(err, locale));
    } finally {
      submitting.current = false;
      setSaving(false);
    }
  }

  async function runAction(item: FeatureItem, action: FeatureAction, input?: string) {
    if (busyRef.current) return;
    const id = `${item.id}:${action.action}`;
    busyRef.current = id;
    setBusy(id);
    setActionError(null);
    try {
      const body: { action: string; expected_revision: number; payload?: Record<string, unknown> } = {
        action: action.action,
        expected_revision: item.revision,
      };
      if (action.input && input !== undefined) {
        body.payload = { [action.input]: toWire(input, action.input_type) ?? "" };
      }
      await commandFeatureItem(config.path, item.id, body, newIdempotencyKey());
      setPending(null);
      setInputValue("");
      setInputError(null);
    } catch (err) {
      setActionError(errorText(err, locale));
    } finally {
      busyRef.current = null;
      setBusy(null);
      // Refresh either way: after a stale-revision error the next click needs the new revision.
      await mutate();
    }
  }

  function startAction(item: FeatureItem, action: FeatureAction) {
    if (!action.input) {
      void runAction(item, action);
      return;
    }
    setPending({ itemId: item.id, action });
    setInputValue("");
    setInputError(null);
  }

  function submitPending(item: FeatureItem, action: FeatureAction) {
    if (action.input_required && !inputValue.trim()) {
      setInputError(t("ui.required", { field: t(`input.${action.input}`) }));
      return;
    }
    if (action.input_type === "number" && !Number.isFinite(Number(inputValue))) {
      setInputError(t("ui.invalidNumber", { field: t(`input.${action.input}`) }));
      return;
    }
    void runAction(item, action, inputValue);
  }

  function renderDerived(item: FeatureItem) {
    const shares = item.data.shares as Shares | undefined;
    const progress = typeof item.data.progress === "number" ? item.data.progress : null;
    const currency = String(item.data.currency ?? baseCurrency);
    return (
      <>
        {shares && shares.length > 0 ? (
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {t("ui.shares")} · {t("ui.participants", { n: shares.length })}
            </p>
            <ul className="mt-1 space-y-1 text-sm">
              {shares.map((share) => (
                <li key={share.name} className="flex justify-between gap-2">
                  <span>{share.name}</span>
                  <span className="tabular-nums">{formatMoney(share.amount, currency)}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
        {progress !== null ? (
          <div>
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
              <span>{t("ui.progress")}</span>
              <span className="tabular-nums">{Math.round(progress * 100)}%</span>
            </div>
            <div
              role="progressbar"
              aria-label={t("ui.progress")}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(progress * 100)}
              className="mt-1 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700"
            >
              <div className="h-full rounded-full bg-brand-600" style={{ width: `${Math.round(progress * 100)}%` }} />
            </div>
            {typeof item.data.remaining === "number" ? (
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {t("ui.remaining")}: <span className="tabular-nums">{formatMoney(Number(item.data.remaining), currency)}</span>
              </p>
            ) : null}
          </div>
        ) : null}
        {item.data.below_watch === true ? (
          <Pill tone="check">{t("ui.belowWatch")}</Pill>
        ) : null}
        {typeof item.data.open_quality_tasks === "number" && item.data.open_quality_tasks > 0 ? (
          <Pill tone="bad">{t("ui.openTasks", { n: item.data.open_quality_tasks })}</Pill>
        ) : null}
      </>
    );
  }

  return (
    <section className="space-y-6" data-testid={`${config.testId}-page`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">{t(`f.${config.key}.title`)}</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{t(`f.${config.key}.description`)}</p>
        </div>
        <button
          type="button"
          className="btn-primary text-sm"
          data-testid={`${config.testId}-primary-action`}
          aria-expanded={adding}
          onClick={() => {
            setAdding((open) => !open);
            setFormError(null);
          }}
        >
          {t(`f.${config.key}.create`)}
        </button>
      </div>

      {header}

      {adding ? (
        <form onSubmit={submit} className="card space-y-4 p-5" aria-label={t(`f.${config.key}.create`)}>
          <div className="grid gap-4 sm:grid-cols-2">
            {config.fields.map((field) => (
              <InputField
                key={field.name}
                id={`${config.testId}-field-${field.name}`}
                label={`${t(`field.${field.name}`)}${field.required ? t("ui.field.requiredMark") : ""}`}
                type={field.type === "money" ? "number" : field.type ?? "text"}
                value={valueOf(field.name)}
                required={field.required}
                onChange={(value) => setValues((current) => ({ ...current, [field.name]: value }))}
              />
            ))}
          </div>
          {formError ? <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">{formError}</p> : null}
          <div className="flex gap-2">
            <button type="submit" className="btn-primary text-sm" disabled={saving}>
              {saving ? t("ui.saving") : t("ui.save")}
            </button>
            <button type="button" className="btn-secondary text-sm" onClick={() => setAdding(false)}>
              {t("ui.cancel")}
            </button>
          </div>
        </form>
      ) : null}

      {actionError ? <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">{actionError}</p> : null}

      {isLoading ? (
        <SkeletonCard className="h-40" />
      ) : error ? (
        <EmptyState title={t("ui.error.title")} description={errorText(error, locale)} />
      ) : items.length === 0 ? (
        <EmptyState title={t("ui.empty.title")} description={t("ui.empty.description")} />
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2" aria-label={t("ui.itemsLabel")}>
          {items.map((item) => {
            const isPending = pending?.itemId === item.id ? pending.action : null;
            return (
              <li key={item.id} className="card flex flex-col gap-4 p-5" data-testid={`${config.testId}-item`}>
                <div className="flex items-start justify-between gap-3">
                  <h2 className="min-w-0 truncate font-semibold text-slate-900 dark:text-slate-100">
                    {item.client_reference}
                  </h2>
                  <Pill tone={featureStatusTone(item.status)} data-testid={`${config.testId}-status`}>
                    {t(`status.${item.status}`)}
                  </Pill>
                </div>
                {STATUS_HINTS.includes(item.status) ? (
                  <p className="-mt-2 text-xs text-slate-600 dark:text-slate-400" data-testid={`${config.testId}-hint`}>
                    {t(`hint.${item.status}`)}
                  </p>
                ) : null}
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  {fields
                    .map((field) => ({ field, text: displayValue(field, item.data[field.name], String(item.data.currency ?? baseCurrency), locale) }))
                    .filter(({ text }) => text !== "")
                    .map(({ field, text }) => (
                      <div key={field.name} className="min-w-0">
                        <dt className="text-xs text-slate-500 dark:text-slate-400">{t(`field.${field.name}`)}</dt>
                        <dd className="break-words text-slate-900 dark:text-slate-100">{text}</dd>
                      </div>
                    ))}
                </dl>
                {renderDerived(item)}
                {isPending ? (
                  <div className="space-y-2 rounded-lg border border-slate-200 p-3 dark:border-slate-700">
                    <InputField
                      id={`${config.testId}-input-${item.id}`}
                      label={t(`input.${isPending.input}`)}
                      type={isPending.input_type}
                      value={inputValue}
                      required={isPending.input_required}
                      onChange={(value) => {
                        setInputValue(value);
                        setInputError(null);
                      }}
                    />
                    {inputError ? <p role="alert" className="text-xs text-rose-700 dark:text-rose-300">{inputError}</p> : null}
                    <div className="flex gap-2">
                      <button
                        type="button"
                        className="btn-primary text-xs"
                        data-testid={`${config.testId}-apply`}
                        disabled={busy !== null}
                        onClick={() => submitPending(item, isPending)}
                      >
                        {t(`action.${isPending.action}`)}
                      </button>
                      <button type="button" className="btn-secondary text-xs" onClick={() => setPending(null)}>
                        {t("ui.cancel")}
                      </button>
                    </div>
                  </div>
                ) : null}
                <div className="mt-auto flex flex-wrap items-center gap-2" role="group" aria-label={t("ui.actionsLabel")}>
                  {item.actions.map((action) => (
                    <button
                      key={action.action}
                      type="button"
                      className="btn-secondary text-xs disabled:cursor-not-allowed disabled:opacity-50"
                      data-testid={`${config.testId}-action-${action.action}`}
                      disabled={busy !== null || action.missing.length > 0}
                      title={
                        action.missing.length > 0
                          ? t("ui.missing", { fields: action.missing.map((f) => t(`field.${f}`)).join(", ") })
                          : undefined
                      }
                      onClick={() => startAction(item, action)}
                    >
                      {t(`action.${action.action}`)}
                    </button>
                  ))}
                  <span className="ml-auto text-xs text-slate-500 dark:text-slate-400">{t("ui.revision", { n: item.revision })}</span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
