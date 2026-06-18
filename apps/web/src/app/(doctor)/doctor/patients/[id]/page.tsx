"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DoctorTimelineSidebar } from "@/components/doctor/doctor-timeline-sidebar";
import { PatientContextPanel } from "@/components/PatientContextPanel";
import { BackLink } from "@/components/ui/back-link";
import { PageHeader } from "@/components/ui/page-header";
import { FlushList, FlushListItem } from "@/components/ui/data-table";
import {
  getProviderPatientBrief,
  getPatientTimeline,
  listEncountersForPatient,
  listProviderPatients,
} from "@/lib/api";
import type { DoctorBrief, Encounter, TimelineEvent } from "@/lib/types";

export default function DoctorPatientPage() {
  const { id } = useParams<{ id: string }>();
  const [brief, setBrief] = useState<DoctorBrief | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [patientName, setPatientName] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getProviderPatientBrief(id).then(setBrief).catch(() => setBrief(null));
    getPatientTimeline(id).then(setTimeline).catch(() => setTimeline([]));
    listEncountersForPatient(id).then(setEncounters).catch(() => setEncounters([]));
    listProviderPatients()
      .then((pts) => {
        const p = pts.find((x) => x.id === id);
        setPatientName(p?.display_name ?? null);
      })
      .catch(() => undefined);
  }, [id]);

  return (
    <>
      <BackLink href="/doctor/patients" label="Patients" />
      <PageHeader title={patientName || "Patient record"} />

      <div className="lg:grid lg:grid-cols-3 lg:gap-6">
        <div className="space-y-6 lg:col-span-2">
          {brief ? (
            <PatientContextPanel
              brief={brief}
              patientName={patientName}
            />
          ) : (
            <p className="text-sm text-text-muted">No health brief on file yet.</p>
          )}

          <section>
            <h2 className="mb-2 font-display text-sm font-semibold text-text">Encounters</h2>
            {encounters.length === 0 ? (
              <p className="text-sm text-text-muted">No encounters yet.</p>
            ) : (
              <FlushList className="rounded-card border border-border bg-surface-raised px-4">
                {encounters.map((e) => (
                  <FlushListItem key={e.id}>
                    <Link
                      href={`/doctor/consultations/${e.id}`}
                      className="flex items-center justify-between text-sm"
                    >
                      <span>
                        <span className="font-semibold capitalize">{e.status}</span>
                        <span className="text-text-muted"> · {e.encounter_type}</span>
                      </span>
                      <span className="text-text-faint" aria-hidden>→</span>
                    </Link>
                  </FlushListItem>
                ))}
              </FlushList>
            )}
          </section>
        </div>

        <aside className="mt-6 lg:mt-0">
          <DoctorTimelineSidebar events={timeline} />
        </aside>
      </div>
    </>
  );
}
