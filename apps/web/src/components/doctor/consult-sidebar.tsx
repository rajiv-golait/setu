"use client";

import { useEffect, useState } from "react";
import { getProviderPatientBrief } from "@/lib/api";
import type { DoctorBrief } from "@/lib/types";

export function ConsultSidebar({ patientId }: { patientId: string }) {
  const [brief, setBrief] = useState<DoctorBrief | null>(null);

  useEffect(() => {
    getProviderPatientBrief(patientId)
      .then(setBrief)
      .catch(() => setBrief(null));
  }, [patientId]);

  if (!brief) {
    return (
      <div className="rounded-card border border-border bg-surface-raised p-4 text-sm text-text-muted">
        Loading patient context…
      </div>
    );
  }

  return (
    <aside className="rounded-card border border-border bg-[#F8F7F2] p-4">
      <p className="text-xs font-bold uppercase text-primary">Assist — context only</p>
      <p className="mt-2 text-sm font-semibold">{brief.one_line}</p>
      <p className="mt-2 text-sm text-text-muted">{brief.chief_concern}</p>
      {brief.suggested_questions.length > 0 && (
        <>
          <p className="mt-4 text-xs font-semibold uppercase text-text-muted">Suggested questions</p>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-sm">
            {brief.suggested_questions.slice(0, 4).map((q) => (
              <li key={q}>{q}</li>
            ))}
          </ul>
        </>
      )}
      <p className="mt-4 text-[11px] italic text-text-faint">
        For practitioner review — not a diagnosis.
      </p>
    </aside>
  );
}
