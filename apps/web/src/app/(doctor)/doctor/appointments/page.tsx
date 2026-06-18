"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AppointmentCard } from "@/components/appointments/appointment-card";
import { RequestQueueCard } from "@/components/doctor/request-queue-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { isToday } from "@/lib/doctor-utils";
import { listAppointments, doctorAppointmentAction } from "@/lib/api";
import type { Appointment } from "@/lib/types";

type Tab = "requests" | "today" | "upcoming" | "completed";

export default function DoctorAppointmentsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-text-muted">Loading appointments…</p>}>
      <DoctorAppointmentsContent />
    </Suspense>
  );
}

function DoctorAppointmentsContent() {
  const searchParams = useSearchParams();
  const [items, setItems] = useState<Appointment[]>([]);
  const [tab, setTab] = useState<Tab>("today");
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const refresh = () => {
    listAppointments().then(setItems).catch(() => setItems([]));
  };

  useEffect(() => {
    refresh();
    const onVisible = () => {
      if (document.visibilityState === "visible") refresh();
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("focus", refresh);
    return () => {
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("focus", refresh);
    };
  }, []);

  useEffect(() => {
    const t = searchParams.get("tab");
    if (t === "requests" || t === "today" || t === "upcoming" || t === "completed") {
      setTab(t);
    }
  }, [searchParams]);

  useEffect(() => {
    const hasRequests = items.some((a) => a.status === "requested");
    if (hasRequests && !searchParams.get("tab")) {
      setTab("requests");
    }
  }, [items, searchParams]);

  const handleAction = async (id: string, action: string, reason?: string) => {
    setBusyId(id);
    setActionError(null);
    try {
      const updated = await doctorAppointmentAction(
        id,
        action,
        reason ? { reason } : undefined,
      );
      setItems((prev) => prev.map((a) => (a.id === id ? updated : a)));
      refresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not update appointment");
      refresh();
    } finally {
      setBusyId(null);
    }
  };

  const requested = useMemo(() => items.filter((a) => a.status === "requested"), [items]);

  const filtered = useMemo(() => {
    if (tab === "requests") return requested;
    if (tab === "completed") return items.filter((a) => a.status === "completed");
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
  }, [items, tab, requested]);

  const sorted = [...filtered].sort((a, b) => {
    if (a.status === "requested" && b.status !== "requested") return -1;
    if (b.status === "requested" && a.status !== "requested") return 1;
    return (b.scheduled_for ?? b.requested_at ?? "").localeCompare(
      a.scheduled_for ?? a.requested_at ?? "",
    );
  });

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: "requests", label: "Requests", count: requested.length },
    { id: "today", label: "Today" },
    { id: "upcoming", label: "Upcoming" },
    { id: "completed", label: "Completed" },
  ];

  return (
    <>
      <ScreenHeader title="Appointments" subtitle="Requests, today's schedule, and history." />
      <div className="mt-4 flex flex-wrap gap-2">
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
            {t.count != null && t.count > 0 ? ` (${t.count})` : ""}
          </button>
        ))}
      </div>
      {actionError && <p className="mt-4 text-sm text-danger">{actionError}</p>}
      <div className="mt-6 space-y-3">
        {sorted.length === 0 ? (
          <p className="text-sm text-text-muted">No appointments in this tab.</p>
        ) : tab === "requests" ? (
          sorted.map((a) => (
            <RequestQueueCard
              key={a.id}
              appt={a}
              busy={busyId === a.id}
              onAccept={() => handleAction(a.id, "accept")}
              onDecline={(reason) => handleAction(a.id, "decline", reason)}
            />
          ))
        ) : (
          sorted.map((a) => (
            <AppointmentCard
              key={a.id}
              appt={a}
              showPatient
              doctorView
              onAction={
                a.status === "requested"
                  ? (action) => handleAction(a.id, action)
                  : undefined
              }
            />
          ))
        )}
      </div>
    </>
  );
}
