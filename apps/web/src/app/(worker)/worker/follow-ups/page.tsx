"use client";

import { useEffect, useState } from "react";
import { WorkerShell } from "@/components/layout/role-shells";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
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
      <PageHeader
        title="Follow-ups"
        subtitle="Upcoming consultations you helped schedule."
      />
      <div className="mt-2 space-y-3">
        {active.map((a) => (
          <AppointmentCard key={a.id} appt={a} showPatient />
        ))}
        {active.length === 0 && (
          <EmptyState
            title="No active follow-ups"
            message="Scheduled visits you helped book will appear here."
          />
        )}
      </div>
    </WorkerShell>
  );
}
