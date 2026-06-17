"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { getProviderMe, listAppointments } from "@/lib/api";
import type { Appointment, ProviderRecord } from "@/lib/types";

export default function DoctorDashboard() {
  const [provider, setProvider] = useState<ProviderRecord | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProviderMe()
      .then(setProvider)
      .catch((e) => setError(e instanceof Error ? e.message : "Not a provider"));
    listAppointments("requested")
      .then(setAppointments)
      .catch(() => setAppointments([]));
  }, []);

  const requested = appointments.filter((a) => a.status === "requested");
  const reviewSoon = appointments.filter(
    (a) => a.triage_id && a.status !== "completed",
  );

  return (
    <div className="animate-setu-fade">
      <h1 className="text-2xl font-semibold">
        {provider?.display_name ? `Dr. ${provider.display_name}` : "Doctor dashboard"}
      </h1>
      {provider?.specialty && (
        <p className="text-sm text-text-muted">{provider.specialty}</p>
      )}
      {error && <p className="mt-2 text-sm text-danger">{error}</p>}

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <div className="rounded-card border border-border bg-surface-raised p-4">
          <p className="text-2xl font-bold text-primary">{requested.length}</p>
          <p className="text-sm text-text-muted">Pending requests</p>
        </div>
        <div className="rounded-card border border-border bg-surface-raised p-4">
          <p className="text-2xl font-bold text-warning">{reviewSoon.length}</p>
          <p className="text-sm text-text-muted">Triage-linked</p>
        </div>
        <Link
          href="/doctor/appointments"
          className="rounded-card border border-primary/30 bg-[#EEF4F0] p-4"
        >
          <p className="font-semibold text-primary">All appointments →</p>
        </Link>
      </div>

      <h2 className="mb-3 mt-8 text-sm font-semibold uppercase text-text-muted">
        Incoming requests
      </h2>
      {requested.length === 0 ? (
        <p className="text-sm text-text-muted">No pending consultation requests.</p>
      ) : (
        <div className="space-y-3">
          {requested.map((a) => (
            <AppointmentCard key={a.id} appt={a} showPatient />
          ))}
        </div>
      )}

      <p className="mt-8 rounded-lg bg-[#F8F7F2] px-3 py-2 text-xs text-text-muted">
        Prepared summaries for practitioner review — not a diagnosis. Clinical decisions remain
        with the treating doctor.
      </p>
    </div>
  );
}
