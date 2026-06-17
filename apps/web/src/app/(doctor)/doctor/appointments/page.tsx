"use client";

import { useEffect, useState } from "react";
import { DoctorShell } from "@/components/layout/role-shells";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { listAppointments, patchAppointment } from "@/lib/api";
import type { Appointment } from "@/lib/types";

export default function DoctorAppointmentsPage() {
  const [items, setItems] = useState<Appointment[]>([]);

  const refresh = () => {
    listAppointments().then(setItems).catch(() => setItems([]));
  };

  useEffect(() => {
    refresh();
  }, []);

  const handleAction = async (id: string, action: string) => {
    await patchAppointment(id, action);
    refresh();
  };

  const sorted = [...items].sort((a, b) => {
    if (a.status === "requested" && b.status !== "requested") return -1;
    if (b.status === "requested" && a.status !== "requested") return 1;
    return (b.requested_at ?? "").localeCompare(a.requested_at ?? "");
  });

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Appointments</h1>
      <div className="mt-6 space-y-3">
        {sorted.map((a) => (
          <AppointmentCard
            key={a.id}
            appt={a}
            showPatient
            onAction={
              a.status === "requested"
                ? (action) => handleAction(a.id, action)
                : undefined
            }
          />
        ))}
      </div>
    </DoctorShell>
  );
}
