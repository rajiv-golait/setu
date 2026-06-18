"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listProviderPatients } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/screen-header";
import { DataTable, DataRow } from "@/components/ui/data-table";

export default function DoctorPatientsPage() {
  const [patients, setPatients] = useState<Array<{ id: string; display_name?: string | null }>>([]);

  useEffect(() => {
    listProviderPatients().then(setPatients).catch(() => setPatients([]));
  }, []);

  return (
    <>
      <ScreenHeader
        title="Patients"
        subtitle="People you have consulted or have upcoming visits with."
      />
      {patients.length === 0 ? (
        <p className="mt-6 text-sm text-text-muted">No patients yet.</p>
      ) : (
        <DataTable className="mt-6">
          {patients.map((p) => (
            <DataRow key={p.id} onClick={() => { window.location.href = `/doctor/patients/${p.id}`; }}>
              <div>
                <p className="font-semibold">{p.display_name || `Patient ${p.id.slice(0, 8)}`}</p>
                <p className="text-sm text-primary">View record →</p>
              </div>
            </DataRow>
          ))}
        </DataTable>
      )}
      <Link href="/doctor" className="mt-6 inline-block text-sm font-semibold text-primary">
        Back to dashboard
      </Link>
    </>
  );
}
