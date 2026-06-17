"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { getAppointmentVisitSummary } from "@/lib/api";
import type { VisitSummary } from "@/lib/api";

export default function VisitSummaryPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [summary, setSummary] = useState<VisitSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAppointmentVisitSummary(id)
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="p-8 text-center text-sm text-text-faint">Loading…</p>;
  if (!summary) return <p className="p-8 text-center text-sm text-danger">Summary not available yet.</p>;

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-4">
      <button
        type="button"
        onClick={() => router.back()}
        className="mb-4 flex items-center gap-2 text-sm font-semibold text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <h1 className="text-xl font-semibold">Visit summary</h1>
      <p className="mt-1 text-sm capitalize text-text-muted">Status: {summary.status}</p>

      {summary.notes.length > 0 && (
        <section className="mt-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Notes</h2>
          <ul className="mt-2 space-y-3">
            {summary.notes.map((n, i) => (
              <li key={i} className="rounded-card border border-border bg-surface-raised p-4 text-sm">
                <p className="text-xs font-semibold uppercase text-primary">{n.note_type}</p>
                <p className="mt-1 whitespace-pre-wrap">{n.body}</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {summary.prescriptions.length > 0 && (
        <section className="mt-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Prescription</h2>
          {summary.prescriptions.map((rx) => {
            const raw = rx.items as Record<string, unknown>;
            const meds = Array.isArray(raw)
              ? raw
              : Array.isArray(raw.medications)
                ? raw.medications
                : [raw];
            return (
              <ul key={rx.id} className="mt-2 space-y-2">
                {meds.map((item, i) => {
                  const row = item as Record<string, string>;
                return (
                  <li
                    key={i}
                    className="rounded-card border border-border bg-surface-raised p-4 text-sm"
                  >
                    <p className="font-semibold">{row.name ?? "Medicine"}</p>
                    <p className="text-text-muted">
                      {[row.dose, row.frequency, row.duration].filter(Boolean).join(" · ")}
                    </p>
                    {row.instructions && <p className="mt-1">{row.instructions}</p>}
                  </li>
                })}
              </ul>
            );
          })}
        </section>
      )}

      <p className="mt-6 rounded-card border border-border bg-[#F4F8F5] p-4 text-xs text-text-muted">
        {summary.disclaimer}
      </p>

      <Link href="/timeline" className="mt-4 block text-center text-sm font-semibold text-primary">
        View health timeline →
      </Link>
    </div>
  );
}
