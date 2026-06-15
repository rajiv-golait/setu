import { Clock, Lock } from "lucide-react";
import { PRIORITY_DISCLAIMER } from "@/lib/constants";
import type { ShareSnapshot } from "@/lib/types";

function formatExpiry(iso?: string | null) {
  if (!iso) return null;
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function DoctorSnapshot({
  snapshot,
  expired = false,
}: {
  snapshot?: ShareSnapshot;
  expired?: boolean;
}) {
  if (expired || !snapshot) {
    return (
      <div className="flex min-h-screen flex-col items-center bg-surface px-6 py-16 text-center animate-setu-fade">
        <div className="flex h-[62px] w-[62px] items-center justify-center rounded-full bg-[#FBF1E3]">
          <Clock className="h-[30px] w-[30px] text-warning" strokeWidth={1.7} />
        </div>
        <h1 className="mt-4 text-[19px] font-semibold">This link has expired</h1>
        <p className="mt-1.5 max-w-[260px] text-sm text-text-muted">
          For privacy, shared briefs expire automatically. Ask the patient to share a new one.
        </p>
        <div className="mt-5 inline-flex items-center gap-2 text-xs text-text-faint">
          <span className="flex h-5 w-5 items-center justify-center rounded-md bg-primary text-[11px] font-bold text-white">
            S
          </span>
          Secured by Setu
        </div>
      </div>
    );
  }

  const { brief, patient_ref, token, expires_at, audience } = snapshot;
  const isSpecialist = audience === "specialist";
  const flagText =
    brief.flags.find((f) => f.type === "abnormal_lab")?.text ??
    brief.chief_concern;

  return (
    <div className="min-h-screen bg-surface animate-setu-fade">
      <div className="flex items-center gap-2 border-b border-[#E2E2DA] bg-[#F2F1EC] px-4 py-2.5">
        <Lock className="h-[13px] w-[13px] text-success" strokeWidth={2} />
        <span className="truncate font-mono text-[12.5px] text-[#5B6B61]">
          setu.health/brief/{token}
        </span>
      </div>

      <div className="px-[18px] pb-8 pt-[18px]">
        <div className="mb-3.5 flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-primary text-[13px] font-bold text-white">
            S
          </span>
          <span className="text-[13px] font-semibold text-[#3D4A42]">
            Setu · Verified snapshot
          </span>
          <span className="ml-auto rounded-full bg-success-bg px-2 py-0.5 text-[11px] font-semibold text-success">
            Read-only
          </span>
        </div>

        {isSpecialist && (
          <div className="mb-3 rounded-card border border-primary-light/30 bg-[#EEF4F0] px-4 py-3">
            <p className="text-xs font-bold uppercase tracking-wide text-primary">
              Specialist handoff
            </p>
            <p className="mt-1 text-sm text-[#2B3830]">
              Shared by the patient&apos;s local doctor for specialist review.
            </p>
          </div>
        )}

        <div className="rounded-hero border border-border bg-surface-raised p-[18px] shadow-card">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight">{patient_ref}</h1>
            <span className="rounded-lg border border-[#E2E2DA] bg-[#F2F1EC] px-2 py-0.5 font-mono text-[13px] font-semibold text-[#5B6B61]">
              ref {token.slice(0, 8)}
            </span>
          </div>
          <p className="mt-1 text-[13.5px] text-text-muted">{brief.one_line}</p>
          {brief.referred_by && (
            <p className="mt-2 text-sm">
              <span className="font-semibold text-text">Referred by:</span>{" "}
              <span className="text-text-muted">{brief.referred_by}</span>
            </p>
          )}
          {brief.specialist_type && (
            <p className="mt-1 inline-flex rounded-full bg-[#EEF4F0] px-2.5 py-0.5 text-xs font-semibold text-primary">
              {brief.specialist_type}
            </p>
          )}
        </div>

        {brief.priority?.level === "review_soon" && (
          <div className="mt-3.5 rounded-card border border-warning-border border-l-4 border-l-warning bg-warning-bg p-3.5">
            <p className="text-xs font-bold uppercase text-warning">Flagged for earlier review</p>
            <ul className="mt-1.5 space-y-0.5">
              {brief.priority.reasons.map((r) => (
                <li key={r} className="text-sm text-[#7C3A06]">
                  {r}
                </li>
              ))}
            </ul>
            <p className="mt-2 text-[11px] italic text-text-faint">{PRIORITY_DISCLAIMER}</p>
          </div>
        )}

        <div className="mt-3.5 rounded-card border border-warning-border border-l-4 border-l-warning bg-[#FBF3E7] p-3.5">
          <p className="text-xs font-bold uppercase tracking-wide text-warning">Needs attention</p>
          <p className="mt-1.5 text-sm font-medium text-[#7C3A06]">{flagText}</p>
        </div>

        <p className="mb-2 mt-5 text-xs font-semibold uppercase tracking-[0.06em] text-[#3D4A42]">
          Latest labs
        </p>
        <div className="overflow-hidden rounded-card border border-border bg-surface-raised">
          {brief.recent_labs.slice(0, 5).map((lab, i) => (
            <div
              key={lab.test}
              className={`flex items-center justify-between px-4 py-2.5 ${i < brief.recent_labs.length - 1 ? "border-b border-[#F2F2EC]" : ""}`}
            >
              <span className="text-sm text-[#2B332D]">{lab.test}</span>
              <div className="flex items-center gap-2 tabular-nums">
                <span className="text-[14.5px] font-bold">
                  {lab.value}
                  {lab.unit ? ` ${lab.unit}` : ""}
                </span>
                {lab.flag && lab.flag !== "normal" && (
                  <span className="min-w-[54px] rounded-full bg-[#FBF1E3] px-2 py-0.5 text-center text-[11px] font-semibold capitalize text-warning">
                    {lab.flag}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>

        <p className="mb-2 mt-5 text-xs font-semibold uppercase tracking-[0.06em] text-[#3D4A42]">
          Current medications
        </p>
        <div className="flex flex-col gap-2">
          {brief.active_medications.slice(0, 4).map((m) => (
            <div
              key={m.name}
              className="rounded-[11px] border border-border bg-surface-raised px-3.5 py-2.5"
            >
              <span className="text-[14.5px] font-semibold">
                {m.name} {m.dose ?? ""}
              </span>
              {m.frequency && (
                <span className="text-[13px] text-text-muted"> · {m.frequency}</span>
              )}
            </div>
          ))}
        </div>

        <div className="mt-6 border-t border-border pt-4 text-center">
          <p className="text-[12.5px] text-text-faint">
            This snapshot was shared by the patient and expires automatically.
          </p>
          {expires_at && (
            <p className="mt-2 text-xs text-warning">Valid until {formatExpiry(expires_at)}</p>
          )}
        </div>
      </div>
    </div>
  );
}
