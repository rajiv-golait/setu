"use client";

import Link from "next/link";
import { Video } from "lucide-react";
import type { Appointment } from "@/lib/types";
import { SecondaryButton } from "@/components/ui/buttons";
import { cn } from "@/lib/cn";

const STATUS_STYLE: Record<string, string> = {
  requested: "bg-warning-bg text-warning",
  accepted: "bg-info-bg text-info",
  confirmed: "bg-success-bg text-success",
  completed: "bg-surface text-text-muted",
  declined: "bg-danger-bg text-danger",
  cancelled: "bg-surface text-text-faint",
};

export function AppointmentCard({
  appt,
  onAction,
  showPatient = false,
}: {
  appt: Appointment;
  onAction?: (action: string) => void;
  showPatient?: boolean;
}) {
  const when = appt.scheduled_for
    ? new Date(appt.scheduled_for).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Time not set";

  return (
    <div className="rounded-card border border-border bg-surface-raised p-4 shadow-card">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold">{appt.specialty}</p>
          {showPatient && (
            <p className="text-xs text-text-muted">Patient {appt.patient_id.slice(0, 12)}…</p>
          )}
          {appt.provider_name && (
            <p className="text-sm text-text-muted">
              {appt.provider_name}
              {appt.provider_specialty ? ` · ${appt.provider_specialty}` : ""}
            </p>
          )}
          <p className="mt-1 text-sm text-text-muted">{when}</p>
        </div>
        <span
          className={cn(
            "shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold capitalize",
            STATUS_STYLE[appt.status] ?? "bg-surface text-text-muted",
          )}
        >
          {appt.status}
        </span>
      </div>

      {appt.consult_room && (appt.status === "accepted" || appt.status === "confirmed") && (
        <Link
          href={
            showPatient
              ? `/doctor/appointments/${appt.id}`
              : `/appointments/${appt.id}`
          }
          className="mt-3 flex items-center gap-2 text-sm font-semibold text-primary"
        >
          <Video className="h-4 w-4" /> Join consultation
        </Link>
      )}

      {onAction && appt.status === "requested" && (
        <div className="mt-3 flex gap-2">
          <SecondaryButton className="flex-1" onClick={() => onAction("accept")}>
            Accept
          </SecondaryButton>
          <SecondaryButton className="flex-1" onClick={() => onAction("decline")}>
            Decline
          </SecondaryButton>
        </div>
      )}
    </div>
  );
}
