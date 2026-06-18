"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { PenLine } from "lucide-react";
import { CancelDialog } from "@/components/appointments/cancel-dialog";
import { RescheduleFlow } from "@/components/appointments/reschedule-flow";
import { DeclineDialog } from "@/components/doctor/decline-dialog";
import { DoctorCaseHeader } from "@/components/doctor/doctor-case-header";
import { DoctorTimelineSidebar } from "@/components/doctor/doctor-timeline-sidebar";
import { VideoConsult } from "@/components/doctor/video-consult";
import { PatientContextPanel } from "@/components/PatientContextPanel";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { BackLink } from "@/components/ui/back-link";
import {
  doctorAppointmentAction,
  getAppointment,
  getAppointmentPatientContext,
  getPatientTimeline,
  listEncountersForPatient,
} from "@/lib/api";
import type { Appointment, PatientContext, TimelineEvent } from "@/lib/types";

const ACTIVE_STATUSES = new Set(["accepted", "confirmed"]);

export default function DoctorAppointmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [appt, setAppt] = useState<Appointment | null>(null);
  const [encounterId, setEncounterId] = useState<string | null>(null);
  const [showReschedule, setShowReschedule] = useState(false);
  const [patientContext, setPatientContext] = useState<PatientContext | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [actionError, setActionError] = useState<string | null>(null);

  const refresh = () => {
    const apptP = getAppointment(id);
    const ctxP = getAppointmentPatientContext(id).catch(() => null);

    Promise.all([apptP, ctxP])
      .then(([found, ctx]) => {
        setAppt(found ?? null);
        setPatientContext(ctx);
        if (found?.patient_id) {
          getPatientTimeline(found.patient_id)
            .then(setTimeline)
            .catch(() => setTimeline([]));
          listEncountersForPatient(found.patient_id)
            .then((encs) => {
              const match = encs.find((e) => e.appointment_id === id);
              if (match) setEncounterId(match.id);
            })
            .catch(() => undefined);
        }
      })
      .catch(() => setAppt(null));
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
  }, [id]);

  const act = async (action: string, opts?: { reason?: string }) => {
    if (!appt) return;
    setActionError(null);
    try {
      const updated = await doctorAppointmentAction(appt.id, action, opts);
      setAppt(updated);
      if (action === "complete" || action === "cancel") {
        setShowReschedule(false);
      }
      refresh();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Could not update appointment");
      refresh();
    }
  };

  const brief = patientContext?.brief as Parameters<typeof PatientContextPanel>[0]["brief"];
  const isActive = appt ? ACTIVE_STATUSES.has(appt.status) : false;

  return (
    <>
      {!appt ? (
        <p className="text-sm text-text-muted">Loading…</p>
      ) : (
        <>
          <BackLink href="/doctor/appointments" label="Appointments" />

          <div className="mt-4 lg:grid lg:grid-cols-3 lg:gap-6">
            <div className="lg:col-span-2">
              <DoctorCaseHeader
                appt={appt}
                chiefConcern={brief?.chief_concern}
                patientName={appt.patient_display_name}
              />

              {actionError && (
                <p className="mt-3 text-sm text-danger">{actionError}</p>
              )}

              <div className="mt-4 flex flex-wrap gap-2">
                {appt.status === "requested" && (
                  <>
                    <PrimaryButton onClick={() => act("accept")}>Accept</PrimaryButton>
                    <DeclineDialog onConfirm={(reason) => act("decline", { reason })} />
                  </>
                )}
                {appt.status === "completed" && (
                  <p className="w-full text-sm font-medium text-success">
                    Consultation completed.
                  </p>
                )}
                <Link
                  href={`/doctor/patients/${appt.patient_id}`}
                  className="inline-flex items-center rounded-full border border-border px-4 py-2 text-sm font-semibold text-primary"
                >
                  Patient record
                </Link>
              </div>

              {appt.consult_room && !["completed", "cancelled", "declined"].includes(appt.status) && (
                <div className="mt-4">
                  <VideoConsult
                    roomName={appt.consult_room}
                    joinLabel="Start video consultation"
                    appointmentId={appt.id}
                    onJoin={() => act("confirm").catch(() => undefined)}
                  />
                </div>
              )}

              {encounterId && (
                <Link
                  href={`/doctor/consultations/${encounterId}`}
                  className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-primary"
                >
                  <PenLine className="h-4 w-4" /> Open consultation notes
                </Link>
              )}

              {patientContext && (
                <div className="mt-6">
                  <PatientContextPanel
                    brief={brief}
                    currentTruth={
                      patientContext.current_truth as Parameters<
                        typeof PatientContextPanel
                      >[0]["currentTruth"]
                    }
                    patientName={appt.patient_display_name}
                    pastBriefs={patientContext.past_briefs}
                    medHistory={patientContext.med_history}
                    labTrends={patientContext.lab_trends}
                    vitalTrends={patientContext.vital_trends}
                  />
                </div>
              )}

              {isActive && (
                <div className="mt-6 space-y-2 border-t border-border pt-4">
                  <SecondaryButton onClick={() => act("complete")}>Mark completed</SecondaryButton>
                  <SecondaryButton
                    onClick={() => act("no_show", { reason: "Patient did not join" })}
                  >
                    Mark no-show
                  </SecondaryButton>
                  <SecondaryButton onClick={() => setShowReschedule((v) => !v)}>
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
                    onConfirm={async (reason) => {
                      await act("cancel", { reason });
                    }}
                  />
                </div>
              )}
            </div>

            <aside className="mt-6 lg:mt-0">
              <DoctorTimelineSidebar events={timeline} />
            </aside>
          </div>

          {encounterId && appt.status !== "completed" && (
            <Link
              href={`/doctor/consultations/${encounterId}`}
              className="fixed bottom-6 right-6 z-40 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-white shadow-lg"
            >
              <PenLine className="h-4 w-4" /> Take notes
            </Link>
          )}
        </>
      )}
    </>
  );
}
