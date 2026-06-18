"use client";

import type { Appointment } from "@/lib/types";
import { patientLabel } from "@/lib/doctor-utils";

export function DoctorCaseHeader({
  appt,
  chiefConcern,
  patientName,
  demographics,
}: {
  appt: Appointment;
  chiefConcern?: string | null;
  patientName?: string | null;
  demographics?: string | null;
}) {
  const name = patientName?.trim() || patientLabel(appt);
  const concern = chiefConcern || appt.chief_concern;

  return (
    <div className="rounded-hero border border-primary/15 bg-[#EAF5F2] p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">Current case</p>
      <h1 className="mt-1 font-display text-2xl font-semibold text-primary">{name}</h1>
      {demographics && <p className="mt-1 text-sm text-text-muted">{demographics}</p>}
      <p className="mt-2 text-sm font-semibold text-text">{appt.specialty}</p>
      {concern && (
        <p className="mt-2 text-sm text-text-muted">
          Here for: <span className="font-medium text-text">{concern}</span>
        </p>
      )}
      <p className="mt-2 capitalize text-xs text-text-faint">Status: {appt.status}</p>
    </div>
  );
}
