"use client";

import { useState } from "react";
import useSWR from "swr";
import { getInboundEmails, receiveEmail } from "@/lib/api";
import type { InboundEmail } from "@/lib/types";
import EmptyState from "@/components/EmptyState";
import { SkeletonCard } from "@/components/Skeleton";
import { formatFileSize } from "@/lib/utils";

export default function InboxPage() {
  const { data, error, isLoading, mutate } = useSWR<{ items: InboundEmail[]; address: string }>(
    "/product/inbound-emails",
    getInboundEmails,
  );
  const [sender, setSender] = useState("");
  const [subject, setSubject] = useState("");
  const [sending, setSending] = useState(false);

  const emails = data?.items ?? [];

  async function simulateEmail() {
    setSending(true);
    try {
      await receiveEmail({
        sender: sender || "sender@example.com",
        subject: subject || "Receipt from example store",
        attachments: [{ filename: "receipt.pdf", content_type: "application/pdf", size: 0 }],
      });
      setSender("");
      setSubject("");
      mutate();
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Email Inbox</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {data?.address
            ? `Forward receipts to ${data.address} and they'll be processed automatically.`
            : "Forward receipts to your inbox address."}
        </p>
      </div>

      {isLoading ? (
        <SkeletonCard className="h-48" />
      ) : error ? (
        <EmptyState icon="⚠️" title="Could not load inbox" description="Check that the backend is running." />
      ) : emails.length === 0 ? (
        <EmptyState icon="📧" title="No emails received" description="Forward receipts to your inbox address — or simulate one below." />
      ) : (
        <ul className="card divide-y divide-slate-100 dark:divide-slate-800" aria-label="Inbound emails">
          {emails.map((email, index) => (
            <li key={`${email.sender}-${email.subject}-${index}`} className="px-5 py-4">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-900 dark:text-slate-100">{email.subject}</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400">from {email.sender}</p>
                </div>
                <span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                  {email.status}
                </span>
              </div>
              {email.attachments.length > 0 ? (
                <ul className="mt-2 space-y-1">
                  {email.attachments.map((attachment) => (
                    <li key={attachment.filename} className="text-xs text-slate-400">
                      📎 {attachment.filename} · {formatFileSize(attachment.size)}
                    </li>
                  ))}
                </ul>
              ) : null}
            </li>
          ))}
        </ul>
      )}

      <section className="card p-5" aria-label="Simulate email">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Simulate inbound email</h2>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Demo helper — sends a fake email into the pipeline.
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <input className="input" placeholder="Sender email" value={sender} onChange={(event) => setSender(event.target.value)} aria-label="Sender email" />
          <input className="input" placeholder="Subject" value={subject} onChange={(event) => setSubject(event.target.value)} aria-label="Subject" />
        </div>
        <button type="button" onClick={simulateEmail} disabled={sending} className="btn-primary mt-4 text-sm">
          {sending ? "Sending…" : "Send simulated email"}
        </button>
      </section>
    </div>
  );
}
