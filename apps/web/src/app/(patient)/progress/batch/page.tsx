"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Check, FileText } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";
import { STAGE_LABELS } from "@/lib/constants";
import { getJob } from "@/lib/api";
import type { JobStatus } from "@/lib/types";

export default function BatchProgressPage() {
  return (
    <Suspense fallback={<div className="px-5 py-8 text-sm text-text-muted">Loading progress…</div>}>
      <BatchProgressContent />
    </Suspense>
  );
}

function BatchProgressContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const jobIds = useMemo(
    () =>
      (searchParams.get("jobs") ?? "")
        .split(",")
        .map((id) => id.trim())
        .filter(Boolean),
    [searchParams],
  );
  const [jobs, setJobs] = useState<Record<string, JobStatus>>({});

  useEffect(() => {
    if (!jobIds.length) return;
    let active = true;

    const poll = async () => {
      const next: Record<string, JobStatus> = {};
      await Promise.all(
        jobIds.map(async (id) => {
          try {
            next[id] = await getJob(id);
          } catch {
            /* keep polling */
          }
        }),
      );
      if (active) setJobs(next);
    };

    void poll();
    const timer = setInterval(poll, 2000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [jobIds]);

  const statuses = jobIds.map((id) => jobs[id]);
  const done = statuses.filter((j) => j?.status === "completed").length;
  const failed = statuses.some((j) => j?.status === "failed");
  const total = jobIds.length;
  const allDone = total > 0 && done === total;

  useEffect(() => {
    if (!allDone) return;
    const t = setTimeout(() => router.push("/summary"), 800);
    return () => clearTimeout(t);
  }, [allDone, router]);

  const aggregateProgress =
    total === 0
      ? 0
      : Math.round(
          (statuses.reduce((sum, j) => sum + (j?.progress ?? 0), 0) / total) * 100,
        );

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">Processing</p>
      <h1 className="text-[23px] font-semibold">
        {failed ? "Some documents need attention" : `Reading ${total} documents`}
      </h1>
      <p className="mt-1 text-sm text-text-muted">
        {done} of {total} complete · {aggregateProgress}% overall
      </p>

      <div className="mt-5 h-2 overflow-hidden rounded-full bg-border">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${aggregateProgress}%` }}
        />
      </div>

      <ul className="mt-6 space-y-3">
        {jobIds.map((id, index) => {
          const job = jobs[id];
          const stage = job?.stage;
          const label = stage ? STAGE_LABELS[stage] ?? stage : "Queued";
          const complete = job?.status === "completed";
          const isFailed = job?.status === "failed";
          return (
            <li
              key={id}
              className="flex items-center gap-3 rounded-card border border-border bg-surface-raised p-3 shadow-card"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[10px] bg-info-bg">
                {complete ? (
                  <Check className="h-5 w-5 text-success" />
                ) : (
                  <FileText className="h-5 w-5 text-info" />
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold">Document {index + 1}</p>
                <p className="text-xs text-text-muted">
                  {isFailed ? "Failed" : complete ? "Done" : label}
                </p>
              </div>
              {complete && (
                <Link
                  href={`/progress/${id}`}
                  className="text-xs font-semibold text-primary"
                >
                  Details
                </Link>
              )}
            </li>
          );
        })}
      </ul>

      {failed && (
        <div className="mt-6">
          <PrimaryButton onClick={() => router.push("/upload")}>Upload again</PrimaryButton>
        </div>
      )}
    </div>
  );
}
