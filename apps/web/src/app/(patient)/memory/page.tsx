"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { getMemory, getReminders, listDocuments } from "@/lib/api";
import { LabSparkline } from "@/components/ui/sparkline";
import { MemorySkeleton } from "@/components/ui/skeleton";
import { ErrorPanel } from "@/components/ui/state-panel";
import { usePatient } from "@/lib/hooks/use-patient";
import type { CurrentTruth, CurrentTruthEntry, ReminderSchedule } from "@/lib/types";

export default function MemoryPage() {
  const { patient, ready } = usePatient();
  const [truth, setTruth] = useState<CurrentTruth | null>(null);
  const [reminders, setReminders] = useState<ReminderSchedule | null>(null);
  const [docCount, setDocCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    setLoading(true);
    Promise.all([
      getMemory(patient.id),
      getReminders(patient.id).catch(() => null),
      listDocuments(patient.id).then((d) => d.length).catch(() => null),
    ])
      .then(([mem, rem, count]) => {
        setTruth(mem);
        setReminders(rem);
        setDocCount(count);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load memory"))
      .finally(() => setLoading(false));
  }, [patient?.id, ready]);

  if (!ready || loading) return <MemorySkeleton />;
  if (error) {
    return (
      <div className="p-5">
        <ErrorPanel title="Couldn't load memory" message={error} retryable onRetry={() => window.location.reload()} />
      </div>
    );
  }
  if (!truth) {
    return (
      <div className="p-5">
        <ErrorPanel title="No memory yet" message="Upload a document to start building your health record." />
        <Link href="/upload" className="mt-4 block text-center text-sm font-semibold text-primary">
          Add document
        </Link>
      </div>
    );
  }

  const meds = truth.entries.filter((e) => e.entry_type === "medication");
  const labs = truth.entries.filter((e) => e.entry_type === "lab_result");
  const conditions = truth.entries.filter((e) => e.entry_type === "diagnosis");
  const allergies = truth.entries.filter((e) => e.entry_type === "allergy");

  const updated = new Date(truth.generated_at).toLocaleString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <h1 className="text-[23px] font-semibold tracking-tight">Health memory</h1>
      <p className="mt-1 text-sm text-text-muted">
        Last updated {updated}
        {docCount != null && docCount > 0 && ` · built from ${docCount} document${docCount === 1 ? "" : "s"}`}
      </p>

      {reminders && reminders.reminders.length > 0 && (
        <MemorySection title="Today's schedule">
          {reminders.reminders.map((r, i) => (
            <div
              key={`${r.type}-${r.label}-${i}`}
              className="rounded-card border border-border bg-surface-raised p-3.5 shadow-card"
            >
              <p className="font-semibold">{r.label}</p>
              {(r.times_of_day?.length ?? 0) > 0 && (
                <p className="mt-1 text-sm text-text-muted">
                  {r.times_of_day!.join(", ")}
                  {r.frequency_text ? ` · ${r.frequency_text}` : ""}
                </p>
              )}
              {r.due_date && (
                <p className="mt-1 text-sm text-text-muted">Due {r.due_date}</p>
              )}
              {r.note && <p className="mt-1 text-xs text-text-faint">{r.note}</p>}
              {r.needs_confirmation && (
                <span className="mt-2 inline-block rounded-full bg-warning-bg px-2 py-0.5 text-[11px] font-semibold text-warning">
                  Confirm with doctor
                </span>
              )}
            </div>
          ))}
          <p className="text-[11px] italic text-text-faint">{reminders.disclaimer}</p>
        </MemorySection>
      )}

      <MemorySection title="Active medications">
        {meds.length === 0 && <EmptyRow text="No medications recorded yet." />}
        {meds.map((e) => (
          <MemoryMedRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

      <MemorySection title="Lab history">
        {labs.length === 0 && <EmptyRow text="No lab results yet." />}
        {labs.map((e) => (
          <MemoryLabRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

      <MemorySection title="Active conditions">
        {conditions.length === 0 && <EmptyRow text="No conditions recorded yet." />}
        {conditions.map((e) => (
          <MemoryCondRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

      <MemorySection title="Allergies">
        {allergies.length === 0 && <EmptyRow text="No allergies recorded." />}
        {allergies.map((e) => (
          <MemoryAllergyRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

      <Link
        href="/vitals"
        className="mt-6 flex items-center justify-center rounded-card border border-dashed border-primary/40 bg-[#EEF4F0] px-4 py-3 text-sm font-semibold text-primary"
      >
        Log blood pressure, sugar, SpO₂ →
      </Link>

      <Link
        href="/upload"
        className="fixed bottom-20 right-5 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-white shadow-[0_8px_20px_rgba(27,67,50,0.28)]"
        aria-label="Add document"
      >
        <Plus className="h-6 w-6" />
      </Link>
    </div>
  );
}

function MemorySection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-6">
      <div className="mb-2 flex items-center gap-2">
        <h2 className="text-[13px] font-semibold uppercase tracking-[0.06em] text-[#3D4A42]">
          {title}
        </h2>
        <div className="h-px flex-1 bg-border" />
      </div>
      <div className="flex flex-col gap-2">{children}</div>
    </section>
  );
}

function EmptyRow({ text }: { text: string }) {
  return (
    <p className="rounded-card border border-border bg-surface-raised p-3.5 text-sm text-text-muted">
      {text}
    </p>
  );
}

function field(entry: CurrentTruthEntry, key: string) {
  const v = entry.value;
  if (v.conflict && Array.isArray(v.values)) return (v.values[0] as Record<string, unknown>)?.[key];
  return v[key];
}

function provenanceChip(entry: CurrentTruthEntry): string | null {
  const v = entry.value;
  const src = v.source ?? v.provenance ?? field(entry, "source");
  if (typeof src === "string" && src) return src;
  return null;
}

function MemoryMedRow({ entry }: { entry: CurrentTruthEntry }) {
  const name = String(field(entry, "name") ?? entry.normalized_key);
  const dose = field(entry, "dose");
  const unit = field(entry, "dose_unit");
  const discontinued = entry.state === "possibly_discontinued";
  const review = entry.state === "needs_review";
  const prov = provenanceChip(entry);
  return (
    <div
      className={`rounded-card border bg-surface-raised p-3.5 shadow-card ${review || discontinued ? "border-l-4 border-l-[#E0B872]" : "border-border"}`}
    >
      <div className="flex flex-wrap items-center gap-2">
        <p className={`font-semibold ${discontinued ? "text-text-muted line-through" : ""}`}>{name}</p>
        {dose != null && (
          <span className="rounded-full bg-[#EEF4F0] px-2 py-0.5 text-xs font-semibold text-primary">
            {String(dose)}
            {unit != null ? String(unit) : ""}
          </span>
        )}
      </div>
      <p className="text-sm text-text-muted">
        {String(field(entry, "frequency") ?? "")}
        {field(entry, "since") ? ` · since ${String(field(entry, "since"))}` : ""}
      </p>
      {prov && (
        <span className="mt-1.5 inline-block rounded-full border border-border bg-[#F2F1EC] px-2 py-0.5 text-[11px] text-text-muted">
          {prov}
        </span>
      )}
      {discontinued && (
        <span className="mt-1 inline-block rounded-full bg-warning-bg px-2 py-0.5 text-[11px] font-semibold text-warning">
          May have stopped
        </span>
      )}
      {review && (
        <span className="mt-1 inline-block rounded-full bg-warning-bg px-2 py-0.5 text-[11px] font-semibold text-warning">
          Check with doctor
        </span>
      )}
    </div>
  );
}

function sparkPoints(entry: CurrentTruthEntry): number[] {
  const history = entry.value.history;
  if (!Array.isArray(history)) return [];
  return history
    .map((h) => {
      const v = (h as Record<string, unknown>).value;
      const n = typeof v === "number" ? v : parseFloat(String(v));
      return Number.isFinite(n) ? n : null;
    })
    .filter((n): n is number => n != null);
}

function MemoryLabRow({ entry }: { entry: CurrentTruthEntry }) {
  const v = entry.value;
  const conflict = entry.state === "conflict" && v.conflict && Array.isArray(v.values);
  const name = String(v.test_name ?? entry.normalized_key);
  const flag = String(v.flag ?? "");
  const trend = v.trend as string | undefined;
  const points = sparkPoints(entry);
  const sparkColor = flag === "high" || flag === "low" ? "#991B1B" : "#40916C";

  if (conflict) {
    const records = v.values as Record<string, unknown>[];
    return (
      <div className="rounded-card border border-l-4 border-l-danger border-border bg-surface-raised p-3.5 shadow-card">
        <span className="font-semibold">{name}</span>
        <div className="mt-2 flex flex-col gap-1.5">
          {records.slice(0, 2).map((rec, i) => (
            <p key={i} className="text-sm text-text-muted">
              Record {String.fromCharCode(65 + i)} {String(rec.value ?? "")}
              {rec.unit ? ` ${String(rec.unit)}` : ""}
              {rec.source ? ` · ${String(rec.source)}` : ""}
            </p>
          ))}
        </div>
        <p className="mt-2 text-xs text-danger">Two different records — confirm with doctor</p>
      </div>
    );
  }

  return (
    <div className="rounded-card border border-border bg-surface-raised p-3.5 shadow-card">
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold">{name}</span>
        <div className="flex items-center gap-2">
          {points.length >= 2 && <LabSparkline points={points} color={sparkColor} />}
          {flag && flag !== "normal" && (
            <span className="rounded-full bg-warning-bg px-2 py-0.5 text-[11px] font-semibold capitalize text-warning">
              {flag}
            </span>
          )}
        </div>
      </div>
      <p className="mt-1 tabular-nums text-sm">
        {String(v.value)}
        {v.unit ? ` ${v.unit}` : ""}
        {trend === "up" && v.previous != null && (
          <span className="ml-2 text-warning">↑ up from {String(v.previous)}</span>
        )}
        {trend === "down" && v.previous != null && (
          <span className="ml-2 text-success">↓ down from {String(v.previous)}</span>
        )}
      </p>
    </div>
  );
}

function MemoryCondRow({ entry }: { entry: CurrentTruthEntry }) {
  const name = String(field(entry, "condition") ?? entry.normalized_key);
  const review = entry.state === "needs_review";
  const status = String(field(entry, "status") ?? "active");
  const resolved = status === "resolved";
  const suspected = status === "suspected";
  const since = field(entry, "since");
  return (
    <div
      className={`flex items-center justify-between rounded-card border bg-surface-raised p-3.5 shadow-card ${
        review || suspected ? "border-l-4 border-l-[#E0B872]" : "border-border"
      }`}
    >
      <div>
        <span className="font-semibold">{name}</span>
        {since != null && since !== "" && (
          <p className="text-xs text-text-muted">since {String(since)}</p>
        )}
      </div>
      <span
        className={`rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ${
          resolved
            ? "bg-[#E8E8E2] text-text-muted"
            : suspected
              ? "bg-warning-bg text-warning"
              : "bg-success-bg text-success"
        }`}
      >
        {resolved ? "Resolved" : suspected ? "Suspected" : status}
      </span>
    </div>
  );
}

function MemoryAllergyRow({ entry }: { entry: CurrentTruthEntry }) {
  const substance = String(field(entry, "substance") ?? entry.normalized_key);
  const severity = String(field(entry, "severity") ?? "");
  const reaction = field(entry, "reaction");
  const severe = severity.toLowerCase() === "severe" || severity.toLowerCase() === "high";
  return (
    <div
      className={`flex flex-wrap items-center gap-2 rounded-card border p-3.5 ${
        severe ? "border-danger-border bg-danger-bg" : "border-border bg-surface-raised"
      }`}
    >
      <span className={`font-semibold ${severe ? "text-[#7A1818]" : ""}`}>{substance}</span>
      {reaction != null && (
        <span className="text-sm text-text-muted">· {String(reaction)}</span>
      )}
      {severity && (
        <span
          className={`ml-auto rounded-full px-2 py-0.5 text-[11px] font-semibold ${
            severe ? "bg-[#F6DCDC] text-[#7A1818]" : "bg-[#EFEFE9] text-text-muted"
          }`}
        >
          {severity}
        </span>
      )}
    </div>
  );
}
