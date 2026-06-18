"use client";

import { useEffect, useState } from "react";
import { listEncountersForPatient, listProviderPatients } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/screen-header";
import { DataTable, DataRow } from "@/components/ui/data-table";
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
    <>
      <ScreenHeader title="Consultation history" subtitle="Past and open visits across your patients." />
      {loading ? (
        <p className="mt-4 text-sm text-text-faint">Loading…</p>
      ) : rows.length === 0 ? (
        <p className="mt-4 text-sm text-text-muted">No consultations yet.</p>
      ) : (
        <DataTable className="mt-6">
          {rows.map((e) => (
            <DataRow key={e.id} onClick={() => { window.location.href = `/doctor/consultations/${e.id}`; }}>
              <div>
                <p className="font-semibold">{e.patient_label}</p>
                <p className="text-sm capitalize text-text-muted">
                  {e.status} · {e.encounter_type}
                </p>
              </div>
            </DataRow>
          ))}
        </DataTable>
      )}
    </>
  );
}
