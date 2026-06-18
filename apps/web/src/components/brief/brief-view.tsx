"use client";

import { useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ChevronDown,
  HelpCircle,
  Info,
  Share2,
  UserCheck,
} from "lucide-react";
import { PrimaryButton, SecondaryButton, SectionHeader } from "@/components/ui/buttons";
import { BriefExportActions } from "@/components/brief/export-actions";
import { ShareBriefCard } from "@/components/brief/share-brief-card";
import { VideoConsult } from "@/components/doctor/video-consult";
import { PRIORITY_DISCLAIMER } from "@/lib/constants";
import type { DoctorBrief } from "@/lib/types";
import { cn } from "@/lib/cn";

function flagStyle(type: string, severity: string) {
  if (type === "conflict" || severity === "critical")
    return {
      bg: "#FBEAEA",
      border: "#EFD2D2",
      accent: "#991B1B",
      titleInk: "#7A1818",
      ink: "#A35454",
      Icon: AlertTriangle,
    };
  if (type === "abnormal_lab" || severity === "warning")
    return {
      bg: "#FBF3E7",
      border: "#ECD8B6",
      accent: "#B45309",
      titleInk: "#7C3A06",
      ink: "#8A5A2B",
      Icon: AlertTriangle,
    };
  return {
    bg: "#E9EFFB",
    border: "#CBD9F2",
    accent: "#2A5BA8",
    titleInk: "#1F3F73",
    ink: "#3A5680",
    Icon: Info,
  };
}

function labAccent(flag?: string | null) {
  if (flag === "high") return { accent: "#991B1B", tint: "#FBEAEA", tag: "High" };
  if (flag === "low") return { accent: "#991B1B", tint: "#FBEAEA", tag: "Low" };
  return { accent: "#166534", tint: "#E7F0E9", tag: "Normal" };
}

function trendArrow(trend?: string | null) {
  if (trend === "up") return { arrow: "▲", ink: "#991B1B" };
  if (trend === "down") return { arrow: "▼", ink: "#166534" };
  return { arrow: "▶", ink: "#9AA0A6" };
}

export function BriefView({
  brief,
  patientName,
  showActions = true,
}: {
  brief: DoctorBrief;
  patientName?: string;
  showActions?: boolean;
}) {
  const [qOpen, setQOpen] = useState(false);

  return (
    <div className="animate-setu-fade px-[18px] pb-6 pt-[18px]">
      <div className="mb-3.5 flex items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-[0.08em] text-primary-light">
          Doctor Brief
        </span>
        <span className="ml-auto text-xs text-text-muted">
          {new Date(brief.generated_at).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
          })}{" "}
          · {brief.model}
        </span>
      </div>

      {/* Lead card */}
      <div className="rounded-hero bg-primary p-5 text-white shadow-raised">
        <div className="flex items-center justify-between gap-3">
          <span className="text-[13.5px] font-semibold text-[#CFE3D6]">
            {patientName ?? "Patient"}
          </span>
          <span className="font-mono text-xs font-semibold tabular-nums text-[#9CC0AE]">
            {brief.patient_id}
          </span>
        </div>
        <p className="mt-2 text-[21px] font-semibold leading-snug tracking-tight">
          {brief.one_line}
        </p>
        <p className="mt-1.5 text-[13.5px] text-[#B9D2C5]">{brief.chief_concern}</p>
      </div>

      <p className="mt-1 text-xs italic text-text-faint">
        Urgent review flags are computed from objective lab values, not AI symptom guessing.
      </p>

      {brief.consult_room && (
        <div className="mt-4 rounded-card border border-primary-light/30 bg-[#EEF4F0] px-4 py-3">
          <p className="text-xs font-bold uppercase tracking-wide text-primary">Video consultation</p>
          <p className="mt-1 text-sm text-[#2B3830]">
            Join when your specialist is ready — same room as on the shared brief link.
          </p>
          <VideoConsult roomName={brief.consult_room} joinLabel="Join your consultation" />
        </div>
      )}

      {/* Referral bridge context */}
      {(brief.referred_by || brief.referral_reason || brief.specialist_type) && (
        <div className="mt-3.5 rounded-card border border-border bg-surface-raised p-4 shadow-card">
          <p className="text-xs font-semibold uppercase tracking-[0.06em] text-primary-light">
            Referral context
          </p>
          {brief.referred_by && (
            <p className="mt-2 text-sm font-semibold text-text">Referred by {brief.referred_by}</p>
          )}
          {brief.referral_reason && (
            <p className="mt-1 text-sm text-text-muted">{brief.referral_reason}</p>
          )}
          {brief.specialist_type && (
            <p className="mt-2 inline-flex rounded-full bg-[#EEF4F0] px-3 py-1 text-xs font-semibold text-primary">
              Suggested: {brief.specialist_type}
            </p>
          )}
        </div>
      )}

      {/* Priority flag (deterministic logistics — not triage) */}
      {brief.priority && brief.priority.level === "review_soon" && (
        <div className="mt-3.5 rounded-card border border-warning-border border-l-4 border-l-warning bg-warning-bg p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-warning">
            Flagged for earlier review
          </p>
          <ul className="mt-2 space-y-1">
            {brief.priority.reasons.map((r) => (
              <li key={r} className="text-sm text-[#7C3A06]">
                {r}
              </li>
            ))}
          </ul>
          <p className="mt-2 text-[11px] italic text-text-faint">{PRIORITY_DISCLAIMER}</p>
        </div>
      )}

      {/* Flags */}
      {brief.flags.length > 0 && (
        <div className="mt-3.5 flex flex-col gap-2.5">
          {brief.flags.map((f, i) => {
            const s = flagStyle(f.type, f.severity);
            const Icon = s.Icon;
            return (
              <div
                key={i}
                className="flex gap-3 rounded-card border border-l-4 p-3.5"
                style={{
                  background: s.bg,
                  borderColor: s.border,
                  borderLeftColor: s.accent,
                }}
              >
                <Icon className="mt-0.5 h-[19px] w-[19px] shrink-0" style={{ color: s.accent }} />
                <p className="text-sm" style={{ color: s.ink }}>
                  {f.text}
                </p>
              </div>
            );
          })}
        </div>
      )}

      <SectionHeader
        title="Active medications"
        badge={`${brief.active_medications.length} active`}
      />
      <div className="flex flex-col gap-2.5">
        {brief.active_medications.map((m) => (
          <div
            key={m.name}
            className="rounded-card border border-border bg-surface-raised p-3.5 shadow-card"
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[15px] font-semibold">{m.name}</span>
              {m.dose && (
                <span className="whitespace-nowrap rounded-lg bg-[#EEF4F0] px-2 py-0.5 text-[13px] font-semibold text-primary">
                  {m.dose}
                </span>
              )}
            </div>
            {m.frequency && (
              <p className="mt-0.5 text-[13px] text-text-muted">{m.frequency}</p>
            )}
          </div>
        ))}
      </div>

      <SectionHeader title="Recent labs" badge="Latest" />
      <div className="flex flex-col gap-2.5">
        {brief.recent_labs.map((lab) => {
          const { accent, tint, tag } = labAccent(lab.flag);
          const { arrow, ink } = trendArrow(lab.trend);
          return (
            <div
              key={lab.test}
              className="rounded-card border border-border border-l-4 bg-surface-raised p-3.5 shadow-card"
              style={{ borderLeftColor: accent }}
            >
              <div className="flex items-baseline justify-between gap-2">
                <span className="text-[14.5px] font-semibold">{lab.test}</span>
                <div className="flex items-baseline gap-1.5 tabular-nums">
                  <span className="text-xl font-bold" style={{ color: accent }}>
                    {lab.value}
                  </span>
                  {lab.unit && <span className="text-xs text-text-muted">{lab.unit}</span>}
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className="rounded-full px-2 py-0.5 text-[11.5px] font-semibold"
                    style={{ color: accent, background: tint }}
                  >
                    {tag}
                  </span>
                  {lab.previous != null && (
                    <span className="text-xs font-bold" style={{ color: ink }}>
                      {arrow} vs {lab.previous}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {brief.active_conditions.length > 0 && (
        <>
          <SectionHeader title="Conditions" />
          <div className="flex flex-col gap-2.5">
            {brief.active_conditions.map((c) => (
              <div
                key={c.condition}
                className="flex items-center gap-3 rounded-card border border-border bg-surface-raised p-3 shadow-card"
              >
                <span className="h-2 w-2 shrink-0 rounded-full bg-primary" />
                <div>
                  <p className="text-[14.5px] font-semibold">{c.condition}</p>
                  {c.since && <p className="text-xs text-text-faint">{c.since}</p>}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {brief.allergies.length > 0 && (
        <>
          <SectionHeader title="Allergies" />
          <div className="flex flex-col gap-2">
            {brief.allergies.map((a) => (
              <div
                key={a.substance}
                className="flex items-center gap-3 rounded-xl border border-danger-border bg-danger-bg p-3"
              >
                <AlertTriangle className="h-4 w-4 shrink-0 text-danger" />
                <span className="text-sm font-semibold text-[#7A1818]">{a.substance}</span>
                {a.severity && (
                  <span className="ml-auto rounded-full bg-[#F6DCDC] px-2 py-0.5 text-[11px] font-semibold text-[#7A1818]">
                    {a.severity}
                  </span>
                )}
              </div>
            ))}
          </div>
        </>
      )}

      {brief.timeline.length > 0 && (
        <>
          <SectionHeader title="Timeline" />
          <div className="rounded-card border border-border bg-surface-raised px-4 py-1 shadow-card">
            {brief.timeline.map((t, i) => (
              <div
                key={`${t.date}-${i}`}
                className={cn(
                  "flex gap-3 py-2.5",
                  i < brief.timeline.length - 1 && "border-b border-[#F2F2EC]",
                )}
              >
                <span className="w-[78px] shrink-0 text-[11.5px] font-semibold tabular-nums text-text-faint">
                  {t.date}
                </span>
                <span className="text-[13.5px] text-[#2B332D]">{t.event}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {brief.suggested_questions.length > 0 && (
        <div className="mt-4 overflow-hidden rounded-[14px] border border-[#E0EAE3] bg-[#F4F8F5]">
          <button
            type="button"
            onClick={() => setQOpen((v) => !v)}
            className="flex w-full items-center gap-3 px-4 py-3.5 text-left"
          >
            <HelpCircle className="h-[18px] w-[18px] text-primary-light" />
            <span className="flex-1 text-[14.5px] font-semibold text-[#234034]">
              Questions to ask your doctor
            </span>
            <ChevronDown
              className={cn("h-[18px] w-[18px] text-[#5B6B61] transition-transform", qOpen && "rotate-180")}
            />
          </button>
          {qOpen && (
            <div className="border-t border-[#E4EDE7] px-1 pb-1">
              {brief.suggested_questions.map((q, i) => (
                <div key={i} className="flex gap-3 border-t border-[#E4EDE7] px-3 py-2.5 first:border-t-0">
                  <span className="text-[13px] font-bold text-primary-light">{i + 1}.</span>
                  <span className="text-sm text-[#2B3830]">{q}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {brief.confidence_notes && (
        <p className="mt-3 px-1 text-xs italic text-text-faint">{brief.confidence_notes}</p>
      )}

      {showActions && (
        <>
          <div className="mb-6">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-primary-light">
              Share with your doctor
            </p>
            <ShareBriefCard
              patientId={brief.patient_id}
              patientName={patientName}
              compact
            />
          </div>

          <BriefExportActions patientId={brief.patient_id} briefId={brief.brief_id} />
          <Link href="/share" className="mt-5 block">
            <PrimaryButton>
              <Share2 className="h-[19px] w-[19px]" aria-hidden />
              Full share screen
            </PrimaryButton>
          </Link>
          <Link href="/referral" className="mt-2.5 block">
            <SecondaryButton>
              <UserCheck className="h-[18px] w-[18px]" aria-hidden />
              Refer to specialist
            </SecondaryButton>
          </Link>
          <p className="mt-2 text-center text-xs text-text-faint">
            Creates a private link a doctor can open
          </p>
        </>
      )}
    </div>
  );
}
