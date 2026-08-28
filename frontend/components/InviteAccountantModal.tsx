"use client";

import { useState } from "react";
import { useTranslation } from "@/lib/i18n";
import Modal from "@/components/Modal";
import { tenantRequest } from "@/lib/api";

interface InviteAccountantModalProps {
  open: boolean;
  onClose: () => void;
}

export default function InviteAccountantModal({ open, onClose }: InviteAccountantModalProps) {
  const { t } = useTranslation();
  const [url, setUrl] = useState<string | null>(null);
  const [expiresAt, setExpiresAt] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function createInvite() {
    setLoading(true);
    setError(null);
    try {
      const res = await tenantRequest<{ url: string; token: string; expires_at: string }>("/api/v1/accountant/invite");
      setUrl(res.url);
      setExpiresAt(res.expires_at);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to create invite";
      if (String(msg).includes("402") || String(msg).toLowerCase().includes("pro required")) {
        setError(t("upgradeToPro"));
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  async function copy() {
    if (!url) return;
    await navigator.clipboard.writeText(url);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <Modal open={open} title={t("inviteCopied")} onClose={onClose}>
      {!url ? (
        <div className="space-y-3">
          <p className="text-sm text-slate-600 dark:text-slate-300">{t("integrationsTitle")}</p>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <button type="button" onClick={createInvite} disabled={loading} className="btn-primary w-full disabled:opacity-50">
            {loading ? "…" : t("syncNow")}
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex gap-2">
            <input readOnly value={url} className="input flex-1 text-xs" aria-label="invite-link" />
            <button type="button" onClick={copy} className="btn-secondary shrink-0">
              {copied ? t("inviteCopied") : "Copy"}
            </button>
          </div>
          {expiresAt ? <p className="text-xs text-slate-500">{expiresAt}</p> : null}
          {copied ? <p className="text-xs font-medium text-emerald-600">{t("inviteCopied")}</p> : null}
        </div>
      )}
    </Modal>
  );
}
