"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { getMemory } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";
import type { CurrentTruth, CurrentTruthEntry } from "@/lib/types";

export default function MemoryPage() {
  const { patient, ready } = usePatient();
  const [truth, setTruth] = useState<CurrentTruth | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready || !patient?.id) return;
    getMemory(patient.id)
      .then(setTruth)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load memory"));
  }, [patient?.id, ready]);

  if (!ready) return <div className="p-5 text-text-faint">Loading…</div>;
  if (error) return <div className="p-5 text-danger">{error}</div>;
  if (!truth) return <div className="p-5 text-text-muted">No memory yet.</div>;

  const meds = truth.entries.filter((e) => e.entry_type === "medication");
  const labs = truth.entries.filter((e) => e.entry_type === "lab_result");
  const conditions = truth.entries.filter((e) => e.entry_type === "diagnosis");
  const allergies = truth.entries.filter((e) => e.entry_type === "allergy");

  return (
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <h1 className="text-[23px] font-semibold tracking-tight">Health memory</h1>
      <p className="mt-1 text-sm text-text-muted">
        Last updated{" "}
        {new Date(truth.generated_at).toLocaleString("en-IN", {
          day: "numeric",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
      </p>

      <MemorySection title="Active medications">
        {meds.map((e) => (
          <MemoryMedRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

      <MemorySection title="Lab history">
        {labs.map((e) => (
          <MemoryLabRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

      <MemorySection title="Active conditions">
        {conditions.map((e) => (
          <MemoryCondRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

      <MemorySection title="Allergies">
        {allergies.map((e) => (
          <MemoryAllergyRow key={e.normalized_key} entry={e} />
        ))}
      </MemorySection>

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

function field(entry: CurrentTruthEntry, key: string) {
  const v = entry.value;
  if (v.conflict && Array.isArray(v.values)) return (v.values[0] as Record<string, unknown>)?.[key];
  return v[key];
}

function MemoryMedRow({ entry }: { entry: CurrentTruthEntry }) {
  const name = String(field(entry, "name") ?? entry.normalized_key);
  const dose = field(entry, "dose");
  const unit = field(entry, "dose_unit");
  const discontinued = entry.state === "possibly_discontinued";
  const review = entry.state === "needs_review";
  return (
    <div
      className={`rounded-card border bg-surface-raised p-3.5 shadow-card ${review || discontinued ? "border-l-4 border-l-[#E0B872]" : "border-border"}`}
    >
      <p className={`font-semibold ${discontinued ? "text-text-muted line-through" : ""}`}>{name}</p>
      <p className="text-sm text-text-muted">
        {dose != null ? String(dose) : ""}
        {unit != null ? String(unit) : ""} · {String(field(entry, "frequency") ?? "")}
      </p>
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

function MemoryLabRow({ entry }: { entry: CurrentTruthEntry }) {
  const v = entry.value;
  const name = String(v.test_name ?? entry.normalized_key);
  const flag = String(v.flag ?? "");
  const trend = v.trend as string | undefined;
  return (
    <div
      className={`rounded-card border bg-surface-raised p-3.5 shadow-card ${entry.state === "conflict" ? "border-l-4 border-l-danger" : "border-border"}`}
    >
      <div className="flex items-center justify-between">
        <span className="font-semibold">{name}</span>
        {flag && flag !== "normal" && (
          <span className="rounded-full bg-warning-bg px-2 py-0.5 text-[11px] font-semibold capitalize text-warning">
            {flag}
          </span>
        )}
      </div>
      <p className="mt-1 tabular-nums text-sm">
        {String(v.value)}
        {v.unit ? ` ${v.unit}` : ""}
        {trend === "up" && v.previous != null && (
          <span className="ml-2 text-warning">↑ up from {String(v.previous)}</span>
        )}
      </p>
      {entry.state === "conflict" && (
        <p className="mt-1 text-xs text-danger">Two different records — confirm with doctor</p>
      )}
    </div>
  );
}

function MemoryCondRow({ entry }: { entry: CurrentTruthEntry }) {
  const name = String(field(entry, "condition") ?? entry.normalized_key);
  const review = entry.state === "needs_review";
  const status = String(field(entry, "status") ?? "active");
  const resolved = status === "resolved";
  return (
    <div
      className={`flex items-center justify-between rounded-card border bg-surface-raised p-3.5 shadow-card ${review ? "border-l-4 border-l-[#E0B872]" : "border-border"}`}
    >
      <span className="font-semibold">{name}</span>
      <span
        className={`rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize ${
          resolved ? "bg-[#E8E8E2] text-text-muted" : "bg-success-bg text-success"
        }`}
      >
        {resolved ? "Resolved" : status}
      </span>
    </div>
  );
}

function MemoryAllergyRow({ entry }: { entry: CurrentTruthEntry }) {
  const substance = String(field(entry, "substance") ?? entry.normalized_key);
  const severity = String(field(entry, "severity") ?? "");
  return (
    <div className="flex items-center gap-2 rounded-card border border-danger-border bg-danger-bg p-3.5">
      <span className="font-semibold text-[#7A1818]">{substance}</span>
      {severity && (
        <span className="ml-auto rounded-full bg-[#F6DCDC] px-2 py-0.5 text-[11px] font-semibold text-[#7A1818]">
          {severity}
        </span>
      )}
    </div>
  );
}
