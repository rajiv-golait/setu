"use client";

import Link from "next/link";
import { PrimaryButton } from "@/components/ui/buttons";
import { DeclineDialog } from "@/components/doctor/decline-dialog";
import { formatWhen, patientLabel } from "@/lib/doctor-utils";
import type { Appointment } from "@/lib/types";
import { cn } from "@/lib/cn";

export function RequestQueueCard({
  appt,
  onAccept,
  onDecline,
  busy = false,
}: {
  appt: Appointment;
  onAccept: () => Promise<void>;
  onDecline: (reason: string) => Promise<void>;
  busy?: boolean;
}) {
  const name = patientLabel(appt);
  const when = formatWhen(appt.scheduled_for ?? appt.requested_at);

  return (
    <div className="rounded-card border border-border bg-surface-raised p-4 shadow-card">
      <Link href={`/doctor/appointments/${appt.id}`} className="block">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-semibold text-text">{name}</p>
            <p className="text-sm text-primary">{appt.specialty}</p>
            {appt.chief_concern && (
              <p className="mt-1 line-clamp-2 text-sm text-text-muted">{appt.chief_concern}</p>
            )}
            <p className="mt-1 text-xs text-text-faint">{when}</p>
          </div>
          <span
            className={cn(
              "shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold capitalize",
              "bg-warning-bg text-warning",
            )}
          >
            {appt.status}
          </span>
        </div>
      </Link>

      {appt.status === "requested" && (
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <PrimaryButton
            className="flex-1"
            disabled={busy}
            onClick={() => onAccept()}
          >
            Accept
          </PrimaryButton>
          <DeclineDialog onConfirm={onDecline} />
        </div>
      )}

      <Link
        href={`/doctor/appointments/${appt.id}`}
        className="mt-2 inline-block text-sm font-semibold text-primary"
      >
        Preview case →
      </Link>
    </div>
  );
}
