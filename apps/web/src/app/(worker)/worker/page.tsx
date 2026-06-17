"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { WorkerShell } from "@/components/layout/role-shells";
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
      <h1 className="text-xl font-semibold">{t("worker.dashboard")}</h1>
      {error && (
        <p className="mt-2 text-sm text-warning">
          {error} — backend health-worker routes pending.
        </p>
      )}
      <div className="mt-6 space-y-3">
        {patients.map((p) => (
          <Link
            key={p.id}
            href={`/worker/patient/${p.id}`}
            className="block rounded-card border border-border bg-surface-raised p-4 shadow-card"
          >
            <p className="font-semibold">{p.display_name ?? "Unnamed patient"}</p>
            <p className="text-sm text-text-muted">
              {p.lang_pref.toUpperCase()}
              {p.is_rural ? " · Rural" : ""}
            </p>
          </Link>
        ))}
        {patients.length === 0 && !error && (
          <p className="text-sm text-text-muted">No assigned patients yet.</p>
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
