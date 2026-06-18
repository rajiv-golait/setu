"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Check, Eye } from "lucide-react";
import { SecondaryButton } from "@/components/ui/buttons";
import { BriefExportActions } from "@/components/brief/export-actions";
import { ensurePatientShare, ApiError } from "@/lib/api";
import type { ShareCreateResponse } from "@/lib/types";

function publicBriefUrl(token: string): string {
  if (typeof window === "undefined") return `/brief/${token}`;
  return `${window.location.origin}/brief/${token}`;
}

type ShareBriefCardProps = {
  patientId: string;
  patientName?: string;
  compact?: boolean;
};

export function ShareBriefCard({ patientId, patientName, compact = false }: ShareBriefCardProps) {
  const [share, setShare] = useState<ShareCreateResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [noBrief, setNoBrief] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    setNoBrief(false);
    try {
      const s = await ensurePatientShare(patientId);
      setShare(s);
    } catch (e) {
      setShare(null);
      if (e instanceof ApiError && e.status === 404) {
        setNoBrief(true);
      } else {
        setError(e instanceof Error ? e.message : "Could not load share link");
      }
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    void load();
  }, [load]);

  const copyLink = async () => {
    if (!share) return;
    const url = share.url.startsWith("http") ? share.url : publicBriefUrl(share.token);
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return <p className="text-center text-sm text-text-faint">Preparing share link…</p>;
  }

  if (noBrief) {
    return (
      <div className="rounded-card border border-border bg-surface-raised p-4 text-center shadow-card">
        <p className="text-sm font-semibold text-text">No doctor brief yet</p>
        <p className="mt-1 text-sm text-text-muted">
          Upload a prescription or lab report first — we&apos;ll generate a brief and share link.
        </p>
        <Link href="/upload" className="mt-3 inline-block text-sm font-semibold text-primary">
          Upload a document →
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-card border border-danger-border bg-danger-bg p-4 text-center">
        <p className="text-sm text-danger">{error}</p>
        <button type="button" onClick={() => void load()} className="mt-2 text-sm font-semibold text-primary">
          Try again
        </button>
      </div>
    );
  }

  if (!share) return null;

  const linkUrl = share.url.startsWith("http") ? share.url : publicBriefUrl(share.token);

  return (
    <div className={compact ? "space-y-3" : "space-y-4"}>
      <div className="rounded-[20px] border border-border bg-surface-raised px-5 pb-5 pt-6 text-center shadow-raised">
        {share.qr_svg ? (
          <div
            role="img"
            aria-label="QR code to share health brief with doctor"
            className="mx-auto flex h-[220px] w-[220px] items-center justify-center [&>svg]:h-full [&>svg]:w-full"
            dangerouslySetInnerHTML={{ __html: share.qr_svg }}
          />
        ) : (
          <div className="mx-auto flex h-[220px] w-[220px] items-center justify-center rounded-2xl bg-[#F4F8F5] text-sm text-text-muted">
            QR unavailable
          </div>
        )}
        <p className="mt-4 text-[13.5px] font-semibold text-primary">
          {patientName ?? "Patient"} · Doctor Brief
        </p>
        {share.expires_at && (
          <p className="mt-2 text-[13px] text-text-muted">
            Valid until{" "}
            <strong>
              {new Date(share.expires_at).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "short",
                year: "numeric",
              })}
            </strong>
          </p>
        )}
      </div>

      <div className="flex items-center gap-2.5 rounded-card border border-border bg-surface-raised py-1.5 pl-4 pr-1.5">
        <div className="min-w-0 flex-1">
          <p className="text-[11px] uppercase tracking-wide text-text-faint">Shareable link</p>
          <p className="truncate font-mono text-[13px] font-semibold text-primary">{linkUrl}</p>
        </div>
        <button
          type="button"
          onClick={() => void copyLink()}
          className="shrink-0 rounded-[10px] bg-[#EEF4F0] px-4 py-2.5 text-[13.5px] font-semibold text-primary"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>

      {!compact && (
        <>
          <div className="rounded-card border border-border bg-surface-raised p-4">
            <p className="text-[13px] font-semibold text-[#3D4A42]">What your doctor will see</p>
            <ul className="mt-3 space-y-2 text-sm text-[#2B332D]">
              {[
                "Conditions & current medications",
                "Latest lab results with trends",
                "Referral context & priority flags",
              ].map((item) => (
                <li key={item} className="flex items-center gap-2.5">
                  <Check className="h-4 w-4 shrink-0 text-success" strokeWidth={2.2} />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <Link href={`/brief/${share.token}?view=specialist`} className="block">
            <SecondaryButton>
              <Eye className="h-[18px] w-[18px]" aria-hidden />
              Preview what the specialist sees
            </SecondaryButton>
          </Link>

          <BriefExportActions shareToken={share.token} briefId={share.share_id} />
        </>
      )}
    </div>
  );
}
