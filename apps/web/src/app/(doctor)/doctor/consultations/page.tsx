"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DoctorShell } from "@/components/layout/role-shells";
import { listEncountersForPatient, listProviderPatients } from "@/lib/api";
import type { Encounter } from "@/lib/types";

type Row = Encounter & { patient_label: string };

export default function DoctorConsultationsPage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const patients = await listProviderPatients();
        const nested = await Promise.all(
          patients.map(async (p) => {
            const encs = await listEncountersForPatient(p.id).catch(() => []);
            return encs.map((e) => ({
              ...e,
              patient_label: p.display_name || p.id.slice(0, 8),
            }));
          }),
        );
        setRows(
          nested
            .flat()
            .sort((a, b) => (b.appointment_id ?? b.id).localeCompare(a.appointment_id ?? a.id)),
        );
      } catch {
        setRows([]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Consultation history</h1>
      {loading ? (
        <p className="mt-4 text-sm text-text-faint">Loading…</p>
      ) : rows.length === 0 ? (
        <p className="mt-4 text-sm text-text-muted">No consultations yet.</p>
      ) : (
        <ul className="mt-6 space-y-3">
          {rows.map((e) => (
            <li key={e.id}>
              <Link
                href={`/doctor/consultations/${e.id}`}
                className="block rounded-card border border-border bg-surface-raised p-4"
              >
                <p className="font-semibold">{e.patient_label}</p>
                <p className="text-sm capitalize text-text-muted">
                  {e.status} · {e.encounter_type}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </DoctorShell>
  );
}
