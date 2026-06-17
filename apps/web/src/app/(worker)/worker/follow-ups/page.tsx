"use client";

import { useEffect, useState } from "react";
import { WorkerShell } from "@/components/layout/role-shells";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { listAppointments } from "@/lib/api";
import type { Appointment } from "@/lib/types";

export default function WorkerFollowUpsPage() {
  const [items, setItems] = useState<Appointment[]>([]);

  useEffect(() => {
    listAppointments()
      .then(setItems)
      .catch(() => setItems([]));
  }, []);

  const active = items.filter((a) => !["completed", "cancelled", "declined"].includes(a.status));

  return (
    <WorkerShell>
      <h1 className="text-xl font-semibold">Follow-ups</h1>
      <p className="mt-1 text-sm text-text-muted">Upcoming consultations you helped schedule.</p>
      <div className="mt-6 space-y-3">
        {active.map((a) => (
          <AppointmentCard key={a.id} appt={a} showPatient />
        ))}
        {active.length === 0 && (
          <p className="text-sm text-text-muted">No active follow-ups.</p>
        )}
      </div>
    </WorkerShell>
  );
}
