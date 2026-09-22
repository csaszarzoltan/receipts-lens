"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { askChat } from "@/lib/api";
import type { ChatQueryResponse } from "@/lib/api";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { useTranslation } from "@/lib/i18n";

/**
 * Chat page (FEAT-049 AI reader-chat).
 *
 * Question input + deterministic read-only answer + sources list +
 * per-source deep-link buttons. EmptyState when no answer yet
 * (tax/page.tsx pattern, useTranslation, Skeleton while loading).
 * No mock data — every answer comes from POST /api/v1/chat/query.
 */
export default function ChatPage() {
  return (
    <Suspense>
      <ChatBody />
    </Suspense>
  );
}

function ChatBody() {
  const { t } = useTranslation();
  const searchParams = useSearchParams();
  const insightParam = searchParams.get("insight");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<ChatQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await askChat(q);
      setAnswer(res);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
          {t("chat")}
        </h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("chatSubtitle")}
        </p>
      </div>

      {insightParam ? (
        <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {insightParam}
        </p>
      ) : null}

      <form onSubmit={submit} className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t("chatPlaceholder")}
          aria-label={t("chat")}
          className="input flex-1"
        />
        <button
          type="submit"
          disabled={loading || question.trim().length === 0}
          className="btn-primary disabled:opacity-50"
        >
          {loading ? "…" : t("askQuestion")}
        </button>
      </form>

      {loading ? <SkeletonCard className="h-48" /> : null}

      {errorMsg ? (
        <EmptyState icon="⚠️" title={t("error")} description={errorMsg} />
      ) : null}

      {!loading && !errorMsg && !answer ? (
        <EmptyState
          icon="💬"
          title={t("chatEmptyTitle")}
          description={t("chatEmptyHint")}
        />
      ) : null}

      {!loading && !errorMsg && answer ? (
        <section className="card space-y-4 p-5" aria-label={t("answerLabel")}>
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              {t("answerLabel")}
            </h2>
            <p className="mt-1 text-slate-900 dark:text-slate-100">
              {answer.answer}
            </p>
          </div>
          {answer.sources.length > 0 ? (
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                {t("sourcesLabel")} ({answer.sources.length})
              </h3>
              <ul className="mt-2 space-y-2">
                {answer.sources.map((src) => (
                  <li
                    key={src.receipt_id}
                    className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800"
                  >
                    <span className="truncate font-mono text-sm">
                      {src.receipt_id}
                    </span>
                    <span className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {src.amount.toLocaleString()} Ft
                      </span>
                      <Link
                        href={`/receipts/${encodeURIComponent(src.receipt_id)}`}
                        className="btn-secondary text-xs"
                      >
                        {t("openInChat")}
                      </Link>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
