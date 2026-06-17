"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DoctorShell } from "@/components/layout/role-shells";
import { getProviderPatientBrief, getPatientTimeline, listEncountersForPatient } from "@/lib/api";
import type { DoctorBrief, Encounter, TimelineEvent } from "@/lib/types";

export default function DoctorPatientPage() {
  const { id } = useParams<{ id: string }>();
  const [brief, setBrief] = useState<DoctorBrief | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);

  useEffect(() => {
    if (!id) return;
    getProviderPatientBrief(id).then(setBrief).catch(() => setBrief(null));
    getPatientTimeline(id).then(setTimeline).catch(() => setTimeline([]));
    listEncountersForPatient(id).then(setEncounters).catch(() => setEncounters([]));
  }, [id]);

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Patient record</h1>
      {brief && (
        <div className="mt-4 rounded-card border border-border bg-surface-raised p-4">
          <p className="font-semibold">{brief.one_line}</p>
          <p className="mt-2 text-sm text-text-muted">{brief.chief_concern}</p>
        </div>
      )}
      <h2 className="mb-2 mt-8 text-sm font-semibold uppercase text-text-muted">Encounters</h2>
      <div className="space-y-2">
        {encounters.map((e) => (
          <Link
            key={e.id}
            href={`/doctor/consultations/${e.id}`}
            className="block rounded-card border border-border p-3 text-sm"
          >
            {e.status} · {e.encounter_type}
          </Link>
        ))}
      </div>
      <h2 className="mb-2 mt-8 text-sm font-semibold uppercase text-text-muted">Timeline</h2>
      <ul className="space-y-2 text-sm">
        {timeline.slice(0, 10).map((t, i) => (
          <li key={i} className="rounded border border-border px-3 py-2">
            <span className="font-semibold">{t.title}</span>
            <span className="ml-2 text-text-muted">
              {new Date(t.at).toLocaleDateString("en-IN")}
            </span>
          </li>
        ))}
      </ul>
    </DoctorShell>
  );
}
