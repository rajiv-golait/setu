"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Check, Eye } from "lucide-react";
import { SecondaryButton } from "@/components/ui/buttons";
import { BriefExportActions } from "@/components/brief/export-actions";
import { VideoConsult } from "@/components/doctor/video-consult";
import { createShare, getBrief } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import type { ShareCreateResponse } from "@/lib/types";

export default function SharePage() {
  const { patient, ready } = usePatient();
  const [share, setShare] = useState<ShareCreateResponse | null>(null);
  const [consultRoom, setConsultRoom] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    setLoading(true);
    Promise.all([createShare(patient.id), getBrief(patient.id).catch(() => null)])
      .then(([s, brief]) => {
        setShare(s);
        setConsultRoom(brief?.consult_room ?? null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Could not create share"))
      .finally(() => setLoading(false));
  }, [patient?.id, ready]);

  const copyLink = async () => {
    if (!share) return;
    const url = share.url.replace("/share/", "/brief/") || `/brief/${share.token}`;
    await navigator.clipboard.writeText(
      url.startsWith("http") ? url : `${window.location.origin}/brief/${share.token}`,
    );
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!ready) return null;

  return (
    <div className="animate-setu-fade px-[18px] pb-8 pt-5">
      <div className="mb-5 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary-light">
          Share with doctor
        </p>
        <h1 className="mt-1 text-[22px] font-semibold tracking-tight">Show this to your doctor</h1>
        <p className="mt-1 text-sm text-text-muted">
          Send the link to a specialist — no app needed.
        </p>
      </div>

      {loading && <p className="text-center text-sm text-text-faint">Creating share link…</p>}
      {error && <p className="mb-4 text-center text-sm text-danger">{error}</p>}

      {share && (
        <>
          <div className="rounded-[20px] border border-border bg-surface-raised px-5 pb-5 pt-6 text-center shadow-raised">
            {share.qr_svg ? (
              <div
                role="img"
                aria-label="QR code to share health brief with doctor"
                className="mx-auto flex h-[260px] w-[260px] animate-setu-pop items-center justify-center [&>svg]:h-full [&>svg]:w-full"
                dangerouslySetInnerHTML={{ __html: share.qr_svg }}
              />
            ) : (
              <div
                role="img"
                aria-label="QR code placeholder"
                className="mx-auto flex h-[260px] w-[260px] animate-setu-pop items-center justify-center rounded-2xl bg-[#F4F8F5]"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-[10px] bg-primary text-xl font-bold text-white">
                  S
                </span>
              </div>
            )}
            <p className="mt-4 text-[13.5px] font-semibold text-primary">
              {patient?.displayName ?? "Patient"} · Doctor Brief
            </p>
            {share.expires_at && (
              <p className="mt-3 inline-flex items-center gap-1.5 rounded-[11px] border border-[#E3EBE5] bg-[#F4F8F5] px-3.5 py-2 text-[13px] text-[#7C3A06]">
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

          <div className="mt-3.5 flex items-center gap-2.5 rounded-card border border-border bg-surface-raised py-1.5 pl-4 pr-1.5">
            <div className="min-w-0 flex-1">
              <p className="text-[11px] uppercase tracking-wide text-text-faint">Or send the link</p>
              <p className="truncate font-mono text-[13.5px] font-semibold text-primary">
                /brief/{share.token}
              </p>
            </div>
            <button
              type="button"
              onClick={copyLink}
              className="shrink-0 rounded-[10px] bg-[#EEF4F0] px-4 py-2.5 text-[13.5px] font-semibold text-primary"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>

          <div className="mt-3.5 rounded-card border border-border bg-surface-raised p-4">
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

          <Link href={`/brief/${share.token}?view=specialist`} className="mt-5 block">
            <SecondaryButton>
              <Eye className="h-[18px] w-[18px]" aria-hidden />
              Preview what the specialist sees
            </SecondaryButton>
          </Link>

          {consultRoom && (
            <div className="mt-4 rounded-card border border-primary-light/30 bg-[#EEF4F0] px-4 py-3">
              <p className="text-xs font-bold uppercase tracking-wide text-primary">Your consultation</p>
              <p className="mt-1 text-sm text-[#2B3830]">
                Use the same room when your specialist joins from the link above.
              </p>
              <VideoConsult roomName={consultRoom} joinLabel="Join your consultation" />
            </div>
          )}

          <BriefExportActions shareToken={share.token} briefId={share.share_id} />
        </>
      )}
    </div>
  );
}
