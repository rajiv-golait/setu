"use client";

import Link from "next/link";
import type { ProviderDashboard } from "@/lib/types";

type StatKey = "pending" | "today" | "completed" | "patients" | "followups";

const STATS: { key: StatKey; label: string; href: string; color: string }[] = [
  { key: "pending", label: "Pending", href: "/doctor/appointments?tab=requests", color: "text-primary" },
  { key: "today", label: "Today", href: "/doctor/appointments?tab=today", color: "text-primary" },
  { key: "completed", label: "Completed", href: "/doctor/appointments?tab=completed", color: "text-success" },
  { key: "patients", label: "Patients", href: "/doctor/patients", color: "text-primary" },
  { key: "followups", label: "Follow-ups", href: "/doctor/consultations", color: "text-warning" },
];

export function DoctorStatPills({
  dash,
  pendingFallback = 0,
}: {
  dash: ProviderDashboard | null;
  pendingFallback?: number;
}) {
  const values: Record<StatKey, number> = {
    pending: dash?.pending_requests ?? pendingFallback,
    today: dash?.today_appointments ?? 0,
    completed: dash?.completed_this_week ?? 0,
    patients: dash?.patient_count ?? 0,
    followups: dash?.follow_ups_due ?? 0,
  };

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {STATS.map(({ key, label, href, color }) => (
        <Link
          key={key}
          href={href}
          className="rounded-card border border-border bg-surface-raised p-4 shadow-card transition hover:border-primary/30"
        >
          <p className={`text-2xl font-bold ${color}`}>{values[key]}</p>
          <p className="text-sm text-text-muted">{label}</p>
        </Link>
      ))}
    </div>
  );
}
