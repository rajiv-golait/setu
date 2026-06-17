"use client";

import { useEffect, useMemo, useState } from "react";
import { DoctorShell } from "@/components/layout/role-shells";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { listAppointments, patchAppointment } from "@/lib/api";
import type { Appointment } from "@/lib/types";

type Tab = "today" | "upcoming" | "completed";

function isToday(iso?: string | null): boolean {
  if (!iso) return false;
  const d = new Date(iso);
  const now = new Date();
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export default function DoctorAppointmentsPage() {
  const [items, setItems] = useState<Appointment[]>([]);
  const [tab, setTab] = useState<Tab>("today");

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

  const filtered = useMemo(() => {
    if (tab === "completed") {
      return items.filter((a) => a.status === "completed");
    }
    if (tab === "today") {
      return items.filter(
        (a) =>
          !["completed", "cancelled", "declined"].includes(a.status) &&
          isToday(a.scheduled_for ?? a.requested_at),
      );
    }
    return items.filter(
      (a) =>
        !["completed", "cancelled", "declined"].includes(a.status) &&
        !isToday(a.scheduled_for ?? a.requested_at),
    );
  }, [items, tab]);

  const sorted = [...filtered].sort((a, b) => {
    if (a.status === "requested" && b.status !== "requested") return -1;
    if (b.status === "requested" && a.status !== "requested") return 1;
    return (b.scheduled_for ?? b.requested_at ?? "").localeCompare(
      a.scheduled_for ?? a.requested_at ?? "",
    );
  });

  const tabs: { id: Tab; label: string }[] = [
    { id: "today", label: "Today" },
    { id: "upcoming", label: "Upcoming" },
    { id: "completed", label: "Completed" },
  ];

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Appointments</h1>
      <div className="mt-4 flex gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-full border px-3 py-1 text-sm font-semibold ${
              tab === t.id ? "border-primary bg-primary text-white" : "border-border"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="mt-6 space-y-3">
        {sorted.length === 0 ? (
          <p className="text-sm text-text-muted">No appointments in this tab.</p>
        ) : (
          sorted.map((a) => (
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
          ))
        )}
      </div>
    </DoctorShell>
  );
}
