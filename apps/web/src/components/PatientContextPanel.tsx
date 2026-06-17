import type { CurrentTruth } from "@/lib/types";

interface BriefData {
  one_line?: string;
  chief_concern?: string;
  active_medications?: Array<{ name?: string; dose?: string; frequency?: string }>;
  recent_labs?: Array<{ test?: string; value?: unknown; unit?: string; flag?: string }>;
  active_conditions?: Array<{ condition?: string }>;
  allergies?: Array<{ substance?: string; severity?: string }>;
  suggested_questions?: string[];
}

interface PatientContextPanelProps {
  brief?: BriefData | null;
  currentTruth?: CurrentTruth | null;
}

export function PatientContextPanel({ brief, currentTruth }: PatientContextPanelProps) {
  if (!brief && !currentTruth) {
    return (
      <div className="rounded-card border border-border bg-surface-raised p-4 text-sm text-text-muted">
        No patient health data on file yet.
      </div>
    );
  }

  const meds = brief?.active_medications ?? [];
  const labs = brief?.recent_labs ?? [];
  const conditions = brief?.active_conditions ?? [];
  const allergies = brief?.allergies ?? [];
  const questions = brief?.suggested_questions ?? [];

  return (
    <div className="space-y-4">
      {brief?.one_line && (
        <div className="rounded-card border border-info-border bg-info-bg p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-info-title">Overview</p>
          <p className="mt-1 text-sm font-semibold text-[#3A5680]">{brief.one_line}</p>
          {brief.chief_concern && (
            <p className="mt-0.5 text-xs text-[#4A6A90]">Concern: {brief.chief_concern}</p>
          )}
        </div>
      )}

      {meds.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary-light">
            Active Medications
          </p>
          <div className="space-y-1.5">
            {meds.map((m, i) => (
              <div key={i} className="rounded-[10px] border border-border bg-surface-raised px-3 py-2">
                <p className="text-sm font-semibold">{m.name ?? "Unknown"}</p>
                <p className="text-xs text-text-muted">
                  {[m.dose, m.frequency].filter(Boolean).join(" · ")}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {labs.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary-light">
            Recent Labs
          </p>
          <div className="space-y-1.5">
            {labs.map((l, i) => {
              const flagColor =
                l.flag === "high"
                  ? "text-danger"
                  : l.flag === "low"
                    ? "text-warning"
                    : "text-text-muted";
              return (
                <div key={i} className="flex items-center justify-between rounded-[10px] border border-border bg-surface-raised px-3 py-2">
                  <p className="text-sm">{l.test ?? "Unknown"}</p>
                  <p className={`text-sm font-semibold ${flagColor}`}>
                    {l.value}{l.unit ? ` ${l.unit}` : ""}
                    {l.flag ? ` (${l.flag})` : ""}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {conditions.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary-light">
            Conditions
          </p>
          <div className="flex flex-wrap gap-2">
            {conditions.map((c, i) => (
              <span key={i} className="rounded-full border border-border bg-surface-raised px-3 py-1 text-xs font-semibold">
                {c.condition}
              </span>
            ))}
          </div>
        </div>
      )}

      {allergies.length > 0 && (
        <div className="rounded-card border border-danger-border bg-danger-bg p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-danger">Allergies</p>
          <ul className="mt-1 space-y-0.5">
            {allergies.map((a, i) => (
              <li key={i} className="text-sm text-danger">
                {a.substance}{a.severity ? ` (${a.severity})` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      {questions.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-primary-light">
            Suggested Questions
          </p>
          <ul className="space-y-1">
            {questions.map((q, i) => (
              <li key={i} className="flex gap-2 text-sm text-text-muted">
                <span>·</span>
                {q}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
