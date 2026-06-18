"use client";

import { useState } from "react";
import { HeartHandshake, Pill, ShieldAlert } from "lucide-react";
import { LabSparkline } from "@/components/ui/sparkline";
import type { CurrentTruth } from "@/lib/types";

interface BriefData {
  one_line?: string;
  chief_concern?: string;
  active_medications?: Array<{ name?: string; dose?: string; frequency?: string; instructions?: string }>;
  recent_labs?: Array<{ test?: string; value?: unknown; unit?: string; flag?: string }>;
  active_conditions?: Array<{ condition?: string }>;
  allergies?: Array<{ substance?: string; severity?: string }>;
  suggested_questions?: string[];
}

interface MedChange { date: string | null; dose: string | null; dose_unit: string | null; frequency: string | null }
interface LabPoint { value: unknown; unit: string | null; date: string | null; flag: string | null }
interface VitalPoint { measured_at: string; value: Record<string, unknown>; flag: string | null }

interface PatientContextPanelProps {
  brief?: BriefData | null;
  currentTruth?: CurrentTruth | null;
  patientName?: string | null;
  pastBriefs?: Array<{ brief_id: string; generated_at: string; one_line: string; chief_concern: string }>;
  medHistory?: Record<string, MedChange[]>;
  labTrends?: Record<string, LabPoint[]>;
  vitalTrends?: Record<string, VitalPoint[]>;
}

export function PatientContextPanel({
  brief, currentTruth, patientName,
  pastBriefs, medHistory, labTrends, vitalTrends,
}: PatientContextPanelProps) {
  if (!brief && !currentTruth) {
    return (
      <div className="rounded-card border border-border bg-surface-raised p-4 text-sm text-text-muted">
        No health record on file yet — this patient hasn&apos;t shared documents.
      </div>
    );
  }

  const meds = brief?.active_medications ?? [];
  const labs = brief?.recent_labs ?? [];
  const conditions = brief?.active_conditions ?? [];
  const allergies = brief?.allergies ?? [];
  const questions = brief?.suggested_questions ?? [];

  return (
    <div className="space-y-4">
      {/* Person-first header */}
      <div className="rounded-hero border border-primary/15 bg-[#EAF5F2] p-4">
        <div className="flex items-center gap-2">
          <HeartHandshake className="h-4 w-4 text-primary" aria-hidden />
          <p className="font-display text-[15px] font-semibold text-primary">
            {patientName?.trim() || "Your patient"}
          </p>
        </div>
        {brief?.one_line && <p className="mt-2 text-sm font-semibold text-text">{brief.one_line}</p>}
        {brief?.chief_concern && (
          <p className="mt-0.5 text-sm text-text-muted">Here for: {brief.chief_concern}</p>
        )}
      </div>

      {meds.length > 0 && (
        <div>
          <SectionLabel>Current medicines</SectionLabel>
          <div className="space-y-1.5">
            {meds.map((m, i) => (
              <div key={i} className="flex items-start gap-2.5 rounded-card border border-border bg-surface-raised px-3 py-2.5">
                <Pill className="mt-0.5 h-4 w-4 shrink-0 text-primary-light" aria-hidden />
                <div className="min-w-0">
                  <p className="text-sm font-semibold">{m.name ?? "Unknown"}</p>
                  <p className="text-xs text-text-muted">
                    {[m.dose, m.frequency, m.instructions].filter(Boolean).join(" · ") || "As prescribed"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {labs.length > 0 && (
        <div>
          <SectionLabel>Recent labs</SectionLabel>
          <div className="space-y-1.5">
            {labs.map((l, i) => {
              const high = l.flag === "high";
              const low = l.flag === "low";
              const flagColor = high ? "text-danger" : low ? "text-warning" : "text-text-muted";
              return (
                <div key={i} className="flex items-center justify-between rounded-card border border-border bg-surface-raised px-3 py-2.5">
                  <p className="text-sm">{l.test ?? "Unknown"}</p>
                  <p className={`text-sm font-semibold ${flagColor}`}>
                    {String(l.value ?? "")}
                    {l.unit ? ` ${l.unit}` : ""}
                    {l.flag ? ` · ${l.flag}` : ""}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {conditions.length > 0 && (
        <div>
          <SectionLabel>Conditions</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {conditions.map((c, i) => (
              <span key={i} className="rounded-full border border-border bg-surface-raised px-3 py-1 text-xs font-semibold">
                {c.condition}
              </span>
            ))}
          </div>
        </div>
      )}

      {allergies.length > 0 && (
        <div className="rounded-card border border-danger-border bg-danger-bg p-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-danger" aria-hidden />
            <p className="text-xs font-semibold uppercase tracking-wide text-danger">Allergies</p>
          </div>
          <ul className="mt-1.5 space-y-0.5">
            {allergies.map((a, i) => (
              <li key={i} className="text-sm text-danger">
                {a.substance}
                {a.severity ? ` (${a.severity})` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      {questions.length > 0 && (
        <div>
          <SectionLabel>Worth asking</SectionLabel>
          <ul className="space-y-1">
            {questions.map((q, i) => (
              <li key={i} className="flex gap-2 text-sm text-text-muted">
                <span className="text-primary-light">·</span>
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}

      <HistorySection
        pastBriefs={pastBriefs}
        medHistory={medHistory}
        labTrends={labTrends}
        vitalTrends={vitalTrends}
      />

      <p className="text-[11px] italic text-text-faint">For your reference — not a diagnosis.</p>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 font-display text-xs font-semibold uppercase tracking-wide text-primary-light">
      {children}
    </p>
  );
}


function HistorySection({
  pastBriefs, medHistory, labTrends, vitalTrends,
}: Pick<PatientContextPanelProps, "pastBriefs" | "medHistory" | "labTrends" | "vitalTrends">) {
  const [open, setOpen] = useState(false);

  const hasBriefs = (pastBriefs?.length ?? 0) > 0;
  const hasMedChanges = Object.keys(medHistory ?? {}).some((k) => (medHistory![k]?.length ?? 0) > 1);
  const hasLabTrends = Object.keys(labTrends ?? {}).length > 0;
  const hasVitalTrends = Object.keys(vitalTrends ?? {}).length > 0;
  if (!hasBriefs && !hasMedChanges && !hasLabTrends && !hasVitalTrends) return null;

  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 py-1 text-left"
        aria-expanded={open}
      >
        <p className="font-display text-xs font-semibold uppercase tracking-wide text-primary-light">
          History
        </p>
        <div className="h-px flex-1 bg-border" />
        <span className="text-[11px] text-text-faint">{open ? "▲" : "▼"}</span>
      </button>

      {open && (
        <div className="mt-2 space-y-3">
          {/* Med changes */}
          {hasMedChanges && (
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                Medicine changes
              </p>
              {Object.entries(medHistory!).map(([key, changes]) =>
                changes.length < 2 ? null : (
                  <div key={key} className="mb-1.5 rounded-card border border-border bg-surface-raised px-3 py-2">
                    <p className="text-xs font-semibold capitalize">{key.replace(/_/g, " ")}</p>
                    {changes.slice(-3).map((c, i) => (
                      <p key={i} className="mt-0.5 text-[11px] text-text-muted">
                        {c.date ?? "—"} · {[c.dose, c.dose_unit, c.frequency].filter(Boolean).join(" ")}
                      </p>
                    ))}
                  </div>
                ),
              )}
            </div>
          )}

          {/* Lab trend sparklines */}
          {hasLabTrends && (
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                Lab trends
              </p>
              {Object.entries(labTrends!).map(([key, pts]) => {
                const nums = pts.map((p) => Number(p.value)).filter((n) => !isNaN(n));
                return (
                  <div key={key} className="mb-1.5 flex items-center justify-between rounded-card border border-border bg-surface-raised px-3 py-2">
                    <p className="text-xs font-semibold capitalize">{key.replace(/_/g, " ")}</p>
                    <div className="flex items-center gap-2">
                      <span className="text-xs tabular-nums text-text-muted">
                        {pts[pts.length - 1]?.value as string ?? ""} {pts[pts.length - 1]?.unit ?? ""}
                      </span>
                      {nums.length >= 2 && <LabSparkline points={nums} />}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Vital trend sparklines */}
          {hasVitalTrends && (
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                Vital trends
              </p>
              {Object.entries(vitalTrends!).map(([vt, pts]) => {
                const nums = pts.map((p) => {
                  const v = p.value;
                  return Number(v.systolic ?? v.fasting ?? v.percent ?? v.bpm ?? NaN);
                }).filter((n) => !isNaN(n));
                if (nums.length < 2) return null;
                return (
                  <div key={vt} className="mb-1.5 flex items-center justify-between rounded-card border border-border bg-surface-raised px-3 py-2">
                    <p className="text-xs font-semibold capitalize">{vt.replace(/_/g, " ")}</p>
                    <LabSparkline points={nums} />
                  </div>
                );
              })}
            </div>
          )}

          {/* Past briefs */}
          {hasBriefs && (
            <div>
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-text-muted">
                Past summaries
              </p>
              {pastBriefs!.slice(0, 3).map((b) => (
                <div key={b.brief_id} className="mb-1.5 rounded-card border border-border bg-surface-raised px-3 py-2">
                  <p className="text-[11px] text-text-muted">
                    {new Date(b.generated_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                  </p>
                  <p className="text-xs font-semibold">{b.one_line || b.chief_concern || "Visit summary"}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
