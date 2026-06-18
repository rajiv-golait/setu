"use client";

import { useCallback, useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/role-shells";
import { BackLink } from "@/components/ui/back-link";
import { DataRow, DataTable } from "@/components/ui/data-table";
import { PageHeader } from "@/components/ui/page-header";
import { listAdminPatients } from "@/lib/api";
import type { PatientRecord } from "@/lib/types";

export default function AdminPatientsPage() {
  const [patients, setPatients] = useState<PatientRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setPatients(await listAdminPatients());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load patients");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AdminShell>
      <PageHeader
        title="Patients"
        subtitle="Registered patients across the platform."
      />
      {error && <p className="mt-4 text-sm text-danger">{error}</p>}
      <div className="mt-6">
        {loading ? (
          <p className="text-sm text-text-faint">Loading…</p>
        ) : patients.length === 0 ? (
          <p className="text-sm text-text-muted">No patients yet.</p>
        ) : (
          <DataTable>
            {patients.map((p) => (
              <DataRow key={p.id}>
                <div>
                  <p className="font-semibold">{p.display_name || "Patient"}</p>
                  <p className="text-sm text-text-muted">{p.id}</p>
                  <p className="mt-1 text-xs text-text-faint">
                    Lang: {p.lang_pref} · Joined {new Date(p.created_at).toLocaleDateString("en-IN")}
                  </p>
                </div>
              </DataRow>
            ))}
          </DataTable>
        )}
      </div>
      <BackLink href="/admin" label="Overview" className="mt-6" />
    </AdminShell>
  );
}
