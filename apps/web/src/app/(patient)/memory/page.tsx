"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { getMemory, getReminders, listDocuments } from "@/lib/api";
import { LabSparkline } from "@/components/ui/sparkline";
import { MemorySkeleton } from "@/components/ui/skeleton";
import { ErrorPanel } from "@/components/ui/state-panel";
import { ScreenHeader } from "@/components/ui/screen-header";
import { SectionHeading } from "@/components/ui/section-heading";
import { medField } from "@/lib/med-utils";
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
    <div className="px-5 pb-24 pt-5">
      <ScreenHeader
        title="Health memory"
        subtitle={
          docCount != null && docCount > 0
            ? `Last updated ${updated} · built from ${docCount} document${docCount === 1 ? "" : "s"}`
            : `Last updated ${updated}`
        }
      />
      <div className="mb-1 flex flex-wrap gap-x-4 gap-y-1 text-sm">
        <Link href="/timeline" className="font-semibold text-primary">
          View timeline →
        </Link>
        <Link href="/profile" className="font-semibold text-primary">
          Health profile →
        </Link>
      </div>

      {reminders && reminders.reminders.length > 0 && (
        <Group title="Today's schedule" footnote={reminders.disclaimer}>
          {reminders.reminders.map((r, i) => (
            <Row key={`${r.type}-${r.label}-${i}`}>
              <p className="font-semibold">{r.label}</p>
              {(r.times_of_day?.length ?? 0) > 0 && (
                <p className="mt-0.5 text-sm text-text-muted">
                  {r.times_of_day!.join(", ")}
                  {r.frequency_text ? ` · ${r.frequency_text}` : ""}
                </p>
              )}
              {r.due_date && <p className="mt-0.5 text-sm text-text-muted">Due {r.due_date}</p>}
              {r.note && <p className="mt-0.5 text-xs text-text-faint">{r.note}</p>}
              {r.needs_confirmation && (
                <Chip tone="warning" className="mt-1.5">
                  Confirm with doctor
                </Chip>
              )}
            </Row>
          ))}
        </Group>
      )}

      <Group title="Active medications" count={meds.length} empty="No medications recorded yet.">
        {meds.map((e) => (
          <MemoryMedRow key={e.normalized_key} entry={e} />
        ))}
      </Group>

      <Group title="Lab history" count={labs.length} empty="No lab results yet.">
        {labs.map((e) => (
          <MemoryLabRow key={e.normalized_key} entry={e} />
        ))}
      </Group>

      <Group title="Active conditions" count={conditions.length} empty="No conditions recorded yet.">
        {conditions.map((e) => (
          <MemoryCondRow key={e.normalized_key} entry={e} />
        ))}
      </Group>

      <Group title="Allergies" count={allergies.length} empty="No allergies recorded.">
        {allergies.map((e) => (
          <MemoryAllergyRow key={e.normalized_key} entry={e} />
        ))}
      </Group>

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

/* --- Layout primitives: one bordered container per section, flush divider rows --- */

function Group({
  title,
  count,
  empty,
  footnote,
  children,
}: {
  title: string;
  count?: number;
  empty?: string;
  footnote?: string;
  children: React.ReactNode;
}) {
  const isEmpty = count === 0;
  return (
    <section className="mt-7">
      <SectionHeading title={title} />
      {isEmpty ? (
        <p className="mt-1.5 text-sm text-text-muted">{empty}</p>
      ) : (
        <ul className="mt-2 divide-y divide-border overflow-hidden rounded-card border border-border bg-surface-raised">
          {children}
        </ul>
      )}
      {footnote && !isEmpty && <p className="mt-1.5 text-[11px] italic text-text-faint">{footnote}</p>}
    </section>
  );
}

/** A flush list row. `accent` paints a thin left rail (review / conflict / severe). */
function Row({
  children,
  accent,
  tinted,
}: {
  children: React.ReactNode;
  accent?: "marigold" | "danger";
  tinted?: boolean;
}) {
  const rail =
    accent === "marigold" ? "bg-marigold" : accent === "danger" ? "bg-danger" : "bg-transparent";
  return (
    <li className={tinted ? "bg-danger-bg" : ""}>
      <div className="flex items-stretch gap-3 px-4 py-3.5">
        <span className={`w-[3px] shrink-0 rounded-full ${rail}`} aria-hidden />
        <div className="min-w-0 flex-1">{children}</div>
      </div>
    </li>
  );
}

function Chip({
  children,
  tone = "muted",
  className = "",
}: {
  children: React.ReactNode;
  tone?: "warning" | "danger" | "success" | "muted";
  className?: string;
}) {
  const tones: Record<string, string> = {
    warning: "bg-warning-bg text-warning",
    danger: "bg-[#F6DCDC] text-[#7A1818]",
    success: "bg-success-bg text-success",
    muted: "bg-[#EFEFE9] text-text-muted",
  };
  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold ${tones[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

function provenanceChip(entry: CurrentTruthEntry): string | null {
  const v = entry.value;
  const src = v.source ?? v.provenance ?? medField(entry, "source");
  if (typeof src === "string" && src) return src;
  return null;
}

function MemoryMedRow({ entry }: { entry: CurrentTruthEntry }) {
  const name = String(medField(entry, "name") ?? entry.normalized_key);
  const dose = medField(entry, "dose");
  const unit = medField(entry, "dose_unit");
  const discontinued = entry.state === "possibly_discontinued";
  const review = entry.state === "needs_review";
  const prov = provenanceChip(entry);
  return (
    <Row accent={review || discontinued ? "marigold" : undefined}>
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
        {String(medField(entry, "frequency") ?? "")}
        {medField(entry, "since") ? ` · since ${String(medField(entry, "since"))}` : ""}
      </p>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {prov && (
          <span className="inline-block rounded-full border border-border bg-[#F2F1EC] px-2 py-0.5 text-[11px] text-text-muted">
            {prov}
          </span>
        )}
        {discontinued && <Chip tone="warning">May have stopped</Chip>}
        {review && <Chip tone="warning">Check with doctor</Chip>}
      </div>
    </Row>
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
      <Row accent="danger">
        <span className="font-semibold">{name}</span>
        <div className="mt-1.5 flex flex-col gap-1">
          {records.slice(0, 2).map((rec, i) => (
            <p key={i} className="text-sm text-text-muted">
              Record {String.fromCharCode(65 + i)} {String(rec.value ?? "")}
              {rec.unit ? ` ${String(rec.unit)}` : ""}
              {rec.source ? ` · ${String(rec.source)}` : ""}
            </p>
          ))}
        </div>
        <p className="mt-1.5 text-xs text-danger">Two different records — confirm with doctor</p>
      </Row>
    );
  }

  return (
    <Row>
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold">{name}</span>
        <div className="flex items-center gap-2">
          {points.length >= 2 && <LabSparkline points={points} color={sparkColor} />}
          {flag && flag !== "normal" && (
            <Chip tone="warning" className="capitalize">
              {flag}
            </Chip>
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
    </Row>
  );
}

function MemoryCondRow({ entry }: { entry: CurrentTruthEntry }) {
  const name = String(medField(entry, "condition") ?? entry.normalized_key);
  const review = entry.state === "needs_review";
  const status = String(medField(entry, "status") ?? "active");
  const resolved = status === "resolved";
  const suspected = status === "suspected";
  const since = medField(entry, "since");
  return (
    <Row accent={review || suspected ? "marigold" : undefined}>
      <div className="flex items-center justify-between gap-2">
        <div>
          <span className="font-semibold">{name}</span>
          {since != null && since !== "" && (
            <p className="text-xs text-text-muted">since {String(since)}</p>
          )}
        </div>
        <Chip tone={resolved ? "muted" : suspected ? "warning" : "success"} className="capitalize">
          {resolved ? "Resolved" : suspected ? "Suspected" : status}
        </Chip>
      </div>
    </Row>
  );
}

function MemoryAllergyRow({ entry }: { entry: CurrentTruthEntry }) {
  const substance = String(medField(entry, "substance") ?? entry.normalized_key);
  const severity = String(medField(entry, "severity") ?? "");
  const reaction = medField(entry, "reaction");
  const severe = severity.toLowerCase() === "severe" || severity.toLowerCase() === "high";
  return (
    <Row accent={severe ? "danger" : undefined} tinted={severe}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={`font-semibold ${severe ? "text-[#7A1818]" : ""}`}>{substance}</span>
        {reaction != null && <span className="text-sm text-text-muted">· {String(reaction)}</span>}
        {severity && (
          <Chip tone={severe ? "danger" : "muted"} className="ml-auto">
            {severity}
          </Chip>
        )}
      </div>
    </Row>
  );
}
