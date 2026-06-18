"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { VideoConsult } from "@/components/doctor/video-consult";
import { CancelDialog } from "@/components/appointments/cancel-dialog";
import { RescheduleFlow } from "@/components/appointments/reschedule-flow";
import { ScreenHeader } from "@/components/ui/screen-header";
import { getAppointment, doctorAppointmentAction } from "@/lib/api";
import { SecondaryButton } from "@/components/ui/buttons";
import type { Appointment } from "@/lib/types";

export default function PatientAppointmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [appt, setAppt] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReschedule, setShowReschedule] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const refresh = () => {
    getAppointment(id)
      .then(setAppt)
      .catch(() => setAppt(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refresh();
  }, [id]);

  const act = async (action: string, opts?: { reason?: string }) => {
    if (!appt) return;
    setActionError(null);
    try {
      const updated = await doctorAppointmentAction(appt.id, action, opts);
      setAppt(updated);
      refresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not update appointment");
      refresh();
    }
  };

  if (loading) return <p className="p-8 text-center text-sm text-text-faint">Loading…</p>;
  if (!appt) return <p className="p-8 text-center text-sm text-danger">Appointment not found</p>;

  const canModify = ["requested", "accepted", "confirmed"].includes(appt.status);

  return (
    <div className="px-5 pb-8 pt-4">
      <ScreenHeader
        mode="toolbar"
        backHref="/appointments"
        title={appt.specialty}
        trailing={
          <span className="rounded-full bg-surface-raised px-2 py-0.5 text-xs font-semibold capitalize text-text-muted">
            {appt.status}
          </span>
        }
      />
      {actionError && <p className="mt-2 text-sm text-danger">{actionError}</p>}

      {appt.status === "completed" && (
        <Link
          href={`/appointments/${appt.id}/summary`}
          className="mt-4 inline-block text-sm font-semibold text-primary"
        >
          View visit summary →
        </Link>
      )}

      {appt.consult_room && appt.status !== "completed" && appt.status !== "cancelled" && (
        <VideoConsult
          roomName={appt.consult_room}
          joinLabel="Join video consultation"
          appointmentId={appt.id}
        />
      )}

      {appt.status === "accepted" && (
        <SecondaryButton className="mt-4" onClick={() => act("confirm")}>
          Confirm attendance
        </SecondaryButton>
      )}

      {canModify && (
        <>
          <SecondaryButton className="mt-4" onClick={() => setShowReschedule((v) => !v)}>
            Reschedule
          </SecondaryButton>
          {showReschedule && appt.provider_id && (
            <RescheduleFlow
              appointmentId={appt.id}
              providerId={appt.provider_id}
              onDone={refresh}
            />
          )}
          <CancelDialog
            key={appt.status}
            disabled={!canModify}
            onConfirm={(reason) => act("cancel", { reason })}
          />
        </>
      )}
    </div>
  );
}
