"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AdminShell } from "@/components/layout/role-shells";
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
      <p className="text-sm text-text-muted">
        Registered patients across the platform. Use worker or patient apps for clinical actions.
      </p>
      {error && <p className="mt-4 text-sm text-danger">{error}</p>}
      <div className="mt-6">
        {loading ? (
          <p className="text-sm text-text-faint">Loading…</p>
        ) : patients.length === 0 ? (
          <p className="text-sm text-text-muted">No patients yet.</p>
        ) : (
          <ul className="space-y-3">
            {patients.map((p) => (
              <li
                key={p.id}
                className="rounded-card border border-border bg-surface-raised p-4"
              >
                <p className="font-semibold">{p.display_name || "Patient"}</p>
                <p className="text-sm text-text-muted">{p.id}</p>
                <p className="mt-1 text-xs text-text-faint">
                  Lang: {p.lang_pref} · Joined {new Date(p.created_at).toLocaleDateString("en-IN")}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
      <p className="mt-6 text-xs text-text-faint">
        <Link href="/admin" className="text-primary">
          ← Back to overview
        </Link>
      </p>
    </AdminShell>
  );
}
