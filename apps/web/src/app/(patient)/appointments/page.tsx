"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { AppointmentCalendar } from "@/components/appointments/appointment-calendar";
import { PrimaryButton } from "@/components/ui/buttons";
import { EmptyState } from "@/components/ui/empty-state";
import { SectionHeading } from "@/components/ui/section-heading";
import { ScreenHeader } from "@/components/ui/screen-header";
import { FlushList, FlushListItem } from "@/components/ui/data-table";
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
    <div className="px-5 pb-8 pt-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ScreenHeader title={t("appointments.title")} />
        <Link href="/appointments/new" className="shrink-0">
          <PrimaryButton className="!w-auto px-4 py-2.5 text-sm">{t("appointments.book")}</PrimaryButton>
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
        <EmptyState
          title={t("appointments.empty")}
          message="Book a visit when you need to see a doctor — your brief travels with the request."
          actionLabel={t("appointments.book")}
          onAction={() => {
            window.location.href = "/appointments/new";
          }}
        />
      )}

      {upcoming.length > 0 && (
        <div className="mt-6">
          <SectionHeading title="Upcoming" />
          <FlushList className="mt-2">
            {upcoming.map((a) => (
              <FlushListItem key={a.id}>
                <AppointmentCard appt={a} />
              </FlushListItem>
            ))}
          </FlushList>
        </div>
      )}

      {past.length > 0 && (
        <div className="mt-6">
          <SectionHeading title="Past visits" />
          <FlushList className="mt-2">
            {past.map((a) => (
              <FlushListItem key={a.id}>
                <AppointmentCard appt={a} />
              </FlushListItem>
            ))}
          </FlushList>
        </div>
      )}
    </div>
  );
}
