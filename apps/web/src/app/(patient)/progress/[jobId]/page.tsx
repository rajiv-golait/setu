"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Check, X } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";
import { STAGE_LABELS } from "@/lib/constants";
import { useJobPolling } from "@/lib/hooks/use-job-polling";

const DISPLAY_STAGES = [
  "extraction",
  "validation",
  "memory",
  "explanation",
  "brief",
  "share",
];

export default function ProgressPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router = useRouter();
  const { job, connState, refresh } = useJobPolling(jobId ?? null);

  useEffect(() => {
    if (job?.status === "completed") {
      const t = setTimeout(() => router.push("/brief"), 800);
      return () => clearTimeout(t);
    }
  }, [job?.status, router]);

  const completed = new Set(job?.completed_stages ?? []);
  const failed = job?.status === "failed";
  const progress = Math.round((job?.progress ?? 0) * 100);

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">Processing</p>
      <h1 className="text-[23px] font-semibold">
        {failed ? "Something went wrong" : "Reading your document"}
      </h1>

      {connState === "retrying" && (
        <div className="mt-3 rounded-card border border-warning-border bg-warning-bg px-3 py-2 text-sm text-warning">
          Connection issue — retrying…
        </div>
      )}
      {connState === "slow" && (
        <div className="mt-3 rounded-card border border-border bg-surface-raised p-3">
          <p className="text-sm text-text-muted">Processing is taking longer than expected</p>
          <button
            type="button"
            onClick={() => refresh()}
            className="mt-2 text-sm font-semibold text-primary"
          >
            Refresh now
          </button>
        </div>
      )}

      <div className="mt-4 h-1 overflow-hidden rounded-full bg-[#E8E8E2]">
        <div
          className="h-full bg-primary-light transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      <ol className="mt-6 space-y-4">
        {DISPLAY_STAGES.map((stage) => {
          const done = completed.has(stage);
          const active = job?.stage === stage && !done && !failed;
          const isFailed = failed && job?.failed_at === stage;
          return (
            <li key={stage} className="flex items-start gap-3">
              <span
                className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 ${
                  isFailed
                    ? "border-danger bg-danger text-white"
                    : done
                      ? "border-primary bg-primary text-white"
                      : active
                        ? "border-primary-light bg-white"
                        : "border-[#D8D8D0] bg-white"
                }`}
              >
                {isFailed ? (
                  <X className="h-4 w-4" />
                ) : done ? (
                  <Check className="h-4 w-4" />
                ) : active ? (
                  <span className="h-2 w-2 animate-pulse-dot rounded-full bg-primary-light" />
                ) : null}
              </span>
              <div>
                <p className="font-semibold capitalize">{stage.replace("_", " ")}</p>
                <p className="text-sm text-text-muted">{STAGE_LABELS[stage] ?? stage}</p>
              </div>
            </li>
          );
        })}
      </ol>

      {job?.status === "completed" && (
        <div className="mt-6 rounded-card border border-success-border bg-success-bg p-4 text-success">
          Your brief is ready — opening now…
        </div>
      )}

      {failed && (
        <>
          <div className="mt-6 rounded-card border border-danger-border bg-danger-bg p-4 text-sm text-danger">
            Couldn&apos;t finish {job?.failed_at ?? "processing"} — earlier steps saved.
            {job?.error?.retryable && " You can try again."}
          </div>
          <Link href="/upload" className="mt-4 block">
            <PrimaryButton>Retry</PrimaryButton>
          </Link>
        </>
      )}
    </div>
  );
}
