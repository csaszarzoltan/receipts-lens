"use client";

import useSWR from "swr";
import { useEffect, useState } from "react";
import { getNotifications, markAllRead, updateNotification } from "@/lib/api";
import type { Notification } from "@/lib/types";
import { timeAgo } from "@/lib/utils";
import { cx } from "@/lib/utils";

/** Slide-over notification center with read/archive actions and unread count. */
export default function NotificationPanel({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { data, error, isLoading, mutate } = useSWR(
    open ? "/product/notifications" : null,
    () => getNotifications(false),
  );
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (open) setDismissed(false);
  }, [open]);

  if (!open) return null;

  const items: Notification[] = data?.items ?? [];
  const unread = data?.unread_count ?? items.filter((item) => !item.read).length;

  async function toggleRead(item: Notification) {
    await updateNotification(item.notification_id, { read: !item.read }).catch(() => undefined);
    mutate();
  }

  async function readAll() {
    await markAllRead().catch(() => undefined);
    mutate();
  }

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Notifications">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close notifications"
      />
      <div className="absolute inset-y-0 right-0 flex w-96 max-w-[90vw] flex-col bg-white shadow-card animate-fade-in dark:bg-slate-950">
        <div className="flex min-h-16 items-center justify-between border-b border-slate-200 px-5 dark:border-slate-800">
          <h2 className="font-semibold text-slate-900 dark:text-slate-100">
            Notifications
            {unread > 0 ? (
              <span className="ml-2 rounded-full bg-brand-600 px-2 py-0.5 text-xs font-medium text-white">
                {unread} new
              </span>
            ) : null}
          </h2>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={readAll}
              className="rounded-lg px-2 py-1 text-xs font-medium text-brand-600 hover:bg-brand-50 dark:text-brand-400 dark:hover:bg-brand-950"
            >
              Mark all read
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <p className="p-6 text-sm text-slate-500 dark:text-slate-400">Loading…</p>
          ) : error ? (
            <p className="p-6 text-sm text-rose-600 dark:text-rose-400">
              Could not load notifications.
            </p>
          ) : items.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-3xl" aria-hidden="true">🔕</p>
              <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                No notifications
              </p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                You're all caught up.
              </p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800">
              {items.map((item) => (
                <li key={item.notification_id}>
                  <button
                    type="button"
                    onClick={() => toggleRead(item)}
                    className={cx(
                      "w-full px-5 py-4 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-900",
                      !item.read && "bg-brand-50/60 dark:bg-brand-950/40",
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={cx(
                          "text-sm font-medium",
                          item.read
                            ? "text-slate-600 dark:text-slate-300"
                            : "text-slate-900 dark:text-slate-100",
                        )}
                      >
                        {item.title}
                      </span>
                      {!item.read ? (
                        <span className="h-2 w-2 shrink-0 rounded-full bg-brand-600" aria-label="Unread" />
                      ) : null}
                    </div>
                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{item.message}</p>
                    <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
                      {timeAgo(item.created_at)}
                    </p>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        {dismissed ? (
          <p className="sr-only" role="status">
            Notification dismissed
          </p>
        ) : null}
      </div>
    </div>
  );
}
