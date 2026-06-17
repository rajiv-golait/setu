"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { DoctorShell } from "@/components/layout/role-shells";
import { CancelDialog } from "@/components/appointments/cancel-dialog";
import { RescheduleFlow } from "@/components/appointments/reschedule-flow";
import { VideoConsult } from "@/components/doctor/video-consult";
import { PatientContextPanel } from "@/components/PatientContextPanel";
import { getAppointment, listEncountersForPatient, patchAppointment } from "@/lib/api";
import { API_BASE } from "@/lib/constants";
import { SecondaryButton } from "@/components/ui/buttons";
import type { Appointment } from "@/lib/types";

export default function DoctorAppointmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [appt, setAppt] = useState<Appointment | null>(null);
  const [encounterId, setEncounterId] = useState<string | null>(null);
  const [showReschedule, setShowReschedule] = useState(false);
  const [patientContext, setPatientContext] = useState<{ brief?: unknown; current_truth?: unknown } | null>(null);

  const refresh = () => {
    const apptP = getAppointment(id);
    const ctxP = fetch(`${API_BASE}/appointments/${id}/patient-context`)
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);

    Promise.all([apptP, ctxP]).then(([found, ctx]) => {
      setAppt(found ?? null);
      setPatientContext(ctx);
      if (found?.patient_id) {
        listEncountersForPatient(found.patient_id)
          .then((encs) => {
            const match = encs.find((e) => e.appointment_id === id);
            if (match) setEncounterId(match.id);
          })
          .catch(() => undefined);
      }
    }).catch(() => setAppt(null));
  };

  useEffect(() => {
    refresh();
  }, [id]);

  const act = async (action: string, opts?: { reason?: string }) => {
    if (!appt) return;
    const updated = await patchAppointment(appt.id, action, opts);
    setAppt(updated);
  };

  return (
    <DoctorShell>
      {!appt ? (
        <p className="text-sm text-text-muted">Loading…</p>
      ) : (
        <>
          <Link href="/doctor/appointments" className="text-sm font-semibold text-primary">
            ← Back
          </Link>
          <h1 className="mt-4 text-xl font-semibold">{appt.specialty}</h1>
          <p className="text-sm text-text-muted">Patient {appt.patient_id}</p>
          <p className="mt-1 capitalize text-sm">Status: {appt.status}</p>
          <Link
            href={`/doctor/patients/${appt.patient_id}`}
            className="mt-2 inline-block text-sm font-semibold text-primary"
          >
            View patient record →
          </Link>

          {appt.status === "requested" && (
            <div className="mt-4 flex gap-2">
              <SecondaryButton onClick={() => act("accept")}>Accept</SecondaryButton>
              <SecondaryButton onClick={() => act("decline")}>Decline</SecondaryButton>
            </div>
          )}

          {appt.consult_room && !["completed", "cancelled", "declined"].includes(appt.status) && (
            <VideoConsult
              roomName={appt.consult_room}
              joinLabel="Start video consultation"
              appointmentId={appt.id}
              onJoin={() => act("confirm").catch(() => undefined)}
            />
          )}

          {encounterId && (
            <Link
              href={`/doctor/consultations/${encounterId}`}
              className="mt-4 inline-block text-sm font-semibold text-primary"
            >
              Open consultation notes →
            </Link>
          )}

          {patientContext && (
            <div className="mt-6">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-primary-light">
                Patient Context
              </p>
              <PatientContextPanel
                brief={patientContext.brief as Parameters<typeof PatientContextPanel>[0]["brief"]}
                currentTruth={patientContext.current_truth as Parameters<typeof PatientContextPanel>[0]["currentTruth"]}
              />
            </div>
          )}

          {["accepted", "confirmed"].includes(appt.status) && (
            <>
              <SecondaryButton className="mt-4" onClick={() => act("complete")}>
                Mark completed
              </SecondaryButton>
              <SecondaryButton
                className="mt-2"
                onClick={() => act("no_show", { reason: "Patient did not join" })}
              >
                Mark no-show
              </SecondaryButton>
              <SecondaryButton className="mt-2" onClick={() => setShowReschedule((v) => !v)}>
                Reschedule
              </SecondaryButton>
              {showReschedule && appt.provider_id && (
                <RescheduleFlow
                  appointmentId={appt.id}
                  providerId={appt.provider_id}
                  onDone={refresh}
                />
              )}
              <CancelDialog onConfirm={(reason) => act("cancel", { reason })} />
            </>
          )}
        </>
      )}
    </DoctorShell>
  );
}
