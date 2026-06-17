"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DoctorShell } from "@/components/layout/role-shells";
import { listProviderPatients } from "@/lib/api";

export default function DoctorPatientsPage() {
  const [patients, setPatients] = useState<Array<{ id: string; display_name?: string | null }>>([]);

  useEffect(() => {
    listProviderPatients().then(setPatients).catch(() => setPatients([]));
  }, []);

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Patients</h1>
      <p className="mt-1 text-sm text-text-muted">People you have consulted or have upcoming visits with.</p>
      <ul className="mt-6 space-y-3">
        {patients.length === 0 ? (
          <li className="text-sm text-text-muted">No patients yet.</li>
        ) : (
          patients.map((p) => (
            <li key={p.id}>
              <Link
                href={`/doctor/patients/${p.id}`}
                className="block w-full rounded-card border border-border bg-surface-raised p-4 text-left"
              >
                <p className="font-semibold">{p.display_name || `Patient ${p.id.slice(0, 8)}`}</p>
                <p className="text-sm text-primary">View record →</p>
              </Link>
            </li>
          ))
        )}
      </ul>
      <Link href="/doctor" className="mt-6 inline-block text-sm font-semibold text-primary">
        Back to dashboard
      </Link>
    </DoctorShell>
  );
}
