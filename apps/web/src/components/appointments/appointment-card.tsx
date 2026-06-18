"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Video } from "lucide-react";
import type { Appointment } from "@/lib/types";
import { SecondaryButton } from "@/components/ui/buttons";
import { formatWhen, patientLabel } from "@/lib/doctor-utils";
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
  doctorView = false,
}: {
  appt: Appointment;
  onAction?: (action: string) => void;
  showPatient?: boolean;
  doctorView?: boolean;
}) {
  const router = useRouter();
  const when = formatWhen(appt.scheduled_for ?? appt.requested_at);
  const detailHref = doctorView
    ? `/doctor/appointments/${appt.id}`
    : `/appointments/${appt.id}`;

  const title = showPatient ? patientLabel(appt) : appt.specialty;
  const subtitle = showPatient ? appt.specialty : null;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => router.push(detailHref)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") router.push(detailHref);
      }}
      className="block cursor-pointer rounded-card border border-border bg-surface-raised p-4 shadow-card transition hover:border-primary/30"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-semibold">{title}</p>
          {subtitle && <p className="text-sm text-text-muted">{subtitle}</p>}
          {showPatient && appt.chief_concern && (
            <p className="mt-1 line-clamp-2 text-xs text-text-muted">{appt.chief_concern}</p>
          )}
          {appt.provider_name && !showPatient && (
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
          href={detailHref}
          className="mt-3 flex items-center gap-2 text-sm font-semibold text-primary"
          onClick={(e) => e.stopPropagation()}
        >
          <Video className="h-4 w-4" /> Join consultation
        </Link>
      )}

      {onAction && appt.status === "requested" && (
        <div
          className="mt-3 flex gap-2"
          onClick={(e) => e.stopPropagation()}
        >
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
