"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { AppointmentCalendar } from "@/components/appointments/appointment-calendar";
import { PrimaryButton } from "@/components/ui/buttons";
import { listAppointments } from "@/lib/api";
import { useLocale } from "@/lib/hooks/use-locale";
import type { Appointment } from "@/lib/types";

export default function AppointmentsPage() {
  const { t } = useLocale();
  const [items, setItems] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAppointments()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Could not load"))
      .finally(() => setLoading(false));
  }, []);

  const upcoming = items.filter((a) => !["completed", "declined", "cancelled"].includes(a.status));
  const past = items.filter((a) => ["completed", "declined", "cancelled"].includes(a.status));

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-5">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-[23px] font-semibold">{t("appointments.title")}</h1>
        <Link href="/appointments/new">
          <PrimaryButton className="!w-auto px-4 py-2 text-sm">{t("appointments.book")}</PrimaryButton>
        </Link>
      </div>

      {loading && <p className="mt-6 text-sm text-text-faint">Loading…</p>}
      {error && <p className="mt-6 text-sm text-danger">{error}</p>}

      {items.length > 0 && (
        <div className="mt-6">
          <AppointmentCalendar appointments={items} />
        </div>
      )}

      {!loading && upcoming.length === 0 && past.length === 0 && (
        <p className="mt-8 text-center text-sm text-text-muted">{t("appointments.empty")}</p>
      )}

      {upcoming.length > 0 && (
        <div className="mt-6 space-y-3">
          <h2 className="text-xs font-semibold uppercase text-text-muted">Upcoming</h2>
          {upcoming.map((a) => (
            <AppointmentCard key={a.id} appt={a} />
          ))}
        </div>
      )}

      {past.length > 0 && (
        <div className="mt-6 space-y-3">
          <h2 className="text-xs font-semibold uppercase text-text-muted">Past</h2>
          {past.map((a) => (
            <AppointmentCard key={a.id} appt={a} />
          ))}
        </div>
      )}
    </div>
  );
}
