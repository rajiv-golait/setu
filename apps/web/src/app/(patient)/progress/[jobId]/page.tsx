"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FileText } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";
import { ErrorPanel } from "@/components/ui/state-panel";
import { PageHeader } from "@/components/ui/page-header";
import { PipelineStepper } from "@/components/ui/pipeline-stepper";
import { WarmCard } from "@/components/ui/warm-card";
import { useJobPolling } from "@/lib/hooks/use-job-polling";
import { formatFileSize, loadUploadMeta, mimeLabel } from "@/lib/upload-meta";
import { retryJob } from "@/lib/api";

export default function ProgressPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const router = useRouter();
  const { job, connState, refresh } = useJobPolling(jobId ?? null);
  const uploadMeta = useMemo(() => loadUploadMeta(), []);
  const [retrying, setRetrying] = useState(false);

  const failed = job?.status === "failed";
  const progress = Math.round((job?.progress ?? 0) * 100);
  const explanation =
    typeof job?.result?.explanation === "string" ? job.result.explanation : null;
  const isLiveAI = job?.result?.source === "live_ai";

  // Auto-redirect on completion after a brief "done" moment.
  useEffect(() => {
    if (job?.status !== "completed") return;
    const docId = job?.result?.document_id as string | undefined;
    const dest = docId ? `/summary?docId=${docId}` : "/summary";
    const t = setTimeout(() => router.push(dest), 600);
    return () => clearTimeout(t);
  }, [job?.status, job?.result?.document_id, router]);

  async function handleRetry() {
    if (!jobId || retrying) return;
    setRetrying(true);
    try {
      await retryJob(jobId);
      refresh();
    } finally {
      setRetrying(false);
    }
  }

  return (
    <div className="px-5 pb-8 pt-5">
      <PageHeader
        eyebrow="Processing"
        title={failed ? "We couldn't read this clearly" : "Reading your document"}
        subtitle={
          failed
            ? "Try a sharper photo or a PDF — good light and all four corners visible helps."
            : "Setu is extracting, validating, and building your health memory."
        }
      />

      {uploadMeta && (
        <WarmCard variant="inset" className="mt-2 flex items-center gap-3 p-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-info-bg">
            <FileText className="h-5 w-5 text-info" strokeWidth={1.7} aria-hidden />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">{uploadMeta.fileName}</p>
            <p className="text-xs text-text-muted">
              {formatFileSize(uploadMeta.size)} · {mimeLabel(uploadMeta.mime)}
            </p>
          </div>
          {isLiveAI && (
            <span className="shrink-0 rounded-full bg-success-bg px-2 py-0.5 text-xs font-semibold text-success">
              AI verified
            </span>
          )}
        </WarmCard>
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

      <div className="mt-6">
        <PipelineStepper
          completedStages={job?.completed_stages ?? []}
          currentStage={job?.stage}
          failedAt={failed ? job?.failed_at : null}
        />
      </div>

      {explanation && (job?.completed_stages ?? []).includes("explanation") && (
        <div className="mt-6 rounded-card border border-info-border bg-info-bg p-4">
          <p className="text-label text-info-title">What we understood</p>
          <p className="mt-2 text-sm leading-relaxed text-[#3A5680]">{explanation}</p>
        </div>
      )}

      {job?.status === "completed" && (
        <div className="mt-6 rounded-card border border-success-border bg-success-bg p-4 text-success text-sm font-semibold">
          Done! Taking you to your summary…
        </div>
      )}

      {failed && (
        <div className="mt-6 space-y-3">
          <ErrorPanel
            title={`Couldn't finish ${job?.failed_at ?? "processing"}`}
            message={job?.error?.message ?? "Earlier steps were saved."}
            code={job?.error?.code}
            retryable={job?.error?.retryable}
            onRetry={job?.error?.retryable ? handleRetry : undefined}
          />
          {!job?.error?.retryable && (
            <Link href="/upload">
              <PrimaryButton>Upload again</PrimaryButton>
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
