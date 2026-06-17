"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/role-shells";
import { getAnalyticsOverview } from "@/lib/api";
import { useLocale } from "@/lib/hooks/use-locale";
import type { AnalyticsOverview } from "@/lib/types";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-card border border-border bg-surface-raised p-4">
      <p className="text-2xl font-bold text-primary">{value}</p>
      <p className="text-sm text-text-muted">{label}</p>
    </div>
  );
}

export default function AdminPage() {
  const { t } = useLocale();
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalyticsOverview()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Analytics API pending"));
  }, []);

  return (
    <AdminShell>
      <p className="text-sm text-text-muted">{t("admin.dashboard")}</p>
      {error && <p className="mt-4 text-sm text-warning">{error}</p>}
      {data && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatCard label="Consultations completed" value={data.consultations_completed} />
          <StatCard label="Rural patients" value={data.rural_patients} />
          <StatCard label="Total patients" value={data.total_patients} />
          <StatCard
            label="Referral completion %"
            value={`${Math.round(data.referral_completion_rate)}%`}
          />
          <StatCard label="High-priority triage" value={data.high_priority_triage} />
          {data.avg_consultation_minutes != null && (
            <StatCard
              label="Avg consult (min)"
              value={Math.round(data.avg_consultation_minutes)}
            />
          )}
        </div>
      )}
      {data?.languages && data.languages.length > 0 && (
        <div className="mt-8">
          <h2 className="mb-3 text-sm font-semibold uppercase text-text-muted">Languages</h2>
          <div className="flex flex-wrap gap-2">
            {data.languages.map((l) => (
              <span
                key={l.lang_pref}
                className="rounded-full border border-border bg-surface-raised px-3 py-1 text-sm"
              >
                {l.lang_pref}: {l.count}
              </span>
            ))}
          </div>
        </div>
      )}
    </AdminShell>
  );
}
