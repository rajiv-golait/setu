"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { WorkerShell } from "@/components/layout/role-shells";
import { ScreenHeader } from "@/components/ui/screen-header";
import { DataTable, DataRow } from "@/components/ui/data-table";
import { EmptyState } from "@/components/ui/empty-state";
import { listWorkerPatients } from "@/lib/api";
import { useLocale } from "@/lib/hooks/use-locale";
import type { AssignedPatient } from "@/lib/types";

export default function WorkerDashboardPage() {
  const { t } = useLocale();
  const [patients, setPatients] = useState<AssignedPatient[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listWorkerPatients()
      .then(setPatients)
      .catch((e) => setError(e instanceof Error ? e.message : "API not ready"));
  }, []);

  return (
    <WorkerShell>
      <ScreenHeader title={t("worker.dashboard")} subtitle="Patients assigned to you at the PHC." />
      {error && (
        <p className="mt-2 text-sm text-warning">
          {error} — backend health-worker routes pending.
        </p>
      )}
      <div className="mt-6 space-y-3">
        {patients.length === 0 && !error ? (
          <EmptyState
            title="No patients yet"
            message="Register a patient or wait for assignments from your supervisor."
            actionLabel="Register patient"
            onAction={() => {
              window.location.href = "/worker/register";
            }}
          />
        ) : (
          <DataTable className="mt-2">
            {patients.map((p) => (
              <DataRow key={p.id} onClick={() => { window.location.href = `/worker/patient/${p.id}`; }}>
                <div>
                  <p className="font-semibold">{p.display_name ?? "Unnamed patient"}</p>
                  <p className="text-sm text-text-muted">
                    {p.lang_pref.toUpperCase()}
                    {p.is_rural ? " · Rural" : ""}
                  </p>
                </div>
              </DataRow>
            ))}
          </DataTable>
        )}
      </div>
      <Link
        href="/worker/register"
        className="mt-6 block text-center text-sm font-semibold text-primary"
      >
        {t("worker.register")} →
      </Link>
    </WorkerShell>
  );
}
