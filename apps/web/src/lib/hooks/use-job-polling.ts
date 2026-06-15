"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getJob } from "@/lib/api";
import type { JobStatus } from "@/lib/types";

export function useJobPolling(jobId: string | null) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [connState, setConnState] = useState<"ok" | "retrying" | "slow">("ok");
  const failCount = useRef(0);
  const activeRef = useRef(true);

  const poll = useCallback(async () => {
    if (!jobId) return;
    try {
      const next = await getJob(jobId);
      setJob(next);
      failCount.current = 0;
      setConnState("ok");
    } catch {
      failCount.current += 1;
      if (failCount.current >= 5) setConnState("slow");
      else if (failCount.current >= 3) setConnState("retrying");
    }
  }, [jobId]);

  useEffect(() => {
    if (!jobId) return;
    activeRef.current = true;

    const tick = async () => {
      if (document.visibilityState === "hidden" || !activeRef.current) return;
      await poll();
    };

    void tick();
    const timer = setInterval(tick, 2000);

    return () => {
      activeRef.current = false;
      clearInterval(timer);
    };
  }, [jobId, poll]);

  return { job, connState, refresh: poll };
}
