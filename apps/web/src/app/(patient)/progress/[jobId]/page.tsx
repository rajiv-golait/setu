"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Check, FileText, X } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";
import { ErrorPanel } from "@/components/ui/state-panel";
import { STAGE_LABELS } from "@/lib/constants";
import { useJobPolling } from "@/lib/hooks/use-job-polling";
import { formatFileSize, loadUploadMeta, mimeLabel } from "@/lib/upload-meta";

const DEFAULT_STAGES = [
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
  const uploadMeta = useMemo(() => loadUploadMeta(), []);

  const stages = job?.stages?.length ? job.stages : DEFAULT_STAGES;
  const completed = new Set(job?.completed_stages ?? []);
  const failed = job?.status === "failed";
  const progress = Math.round((job?.progress ?? 0) * 100);
  const explanation =
    typeof job?.result?.explanation === "string" ? job.result.explanation : null;

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">Processing</p>
      <h1 className="text-[23px] font-semibold">
        {failed ? "Something went wrong" : "Reading your document"}
      </h1>

      {uploadMeta && (
        <div className="mt-4 flex items-center gap-3 rounded-card border border-border bg-surface-raised p-3 shadow-card">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-info-bg">
            <FileText className="h-5 w-5 text-info" strokeWidth={1.7} aria-hidden />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">{uploadMeta.fileName}</p>
            <p className="text-xs text-text-muted">
              {formatFileSize(uploadMeta.size)} · {mimeLabel(uploadMeta.mime)}
            </p>
          </div>
        </div>
      )}

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
        {stages.map((stage) => {
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

      {explanation && completed.has("explanation") && (
        <div className="mt-6 rounded-card border border-info-border bg-info-bg p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-info-title">
            What we understood
          </p>
          <p className="mt-2 text-sm leading-relaxed text-[#3A5680]">{explanation}</p>
        </div>
      )}

      {job?.status === "completed" && (
        <div className="mt-6 space-y-3">
          <div className="rounded-card border border-success-border bg-success-bg p-4 text-success">
            Your explanation is ready.
          </div>
          <PrimaryButton onClick={() => router.push("/summary")}>
            Read your summary
          </PrimaryButton>
          <button
            type="button"
            onClick={() => router.push("/brief")}
            className="flex min-h-[44px] w-full items-center justify-center rounded-[13px] border border-border bg-surface-raised text-base font-semibold text-primary"
          >
            View doctor brief
          </button>
        </div>
      )}

      {failed && (
        <div className="mt-6 space-y-3">
          <ErrorPanel
            title={`Couldn't finish ${job?.failed_at ?? "processing"}`}
            message={job?.error?.message ?? "Earlier steps were saved."}
            code={job?.error?.code}
            retryable={job?.error?.retryable}
            onRetry={() => router.push("/upload")}
          />
          {!job?.error?.retryable && (
            <Link href="/upload">
              <PrimaryButton>Retry</PrimaryButton>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
