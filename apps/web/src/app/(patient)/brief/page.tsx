"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getBrief } from "@/lib/api";
import { BriefView } from "@/components/brief/brief-view";
import { BriefSkeleton } from "@/components/ui/skeleton";
import { ErrorPanel } from "@/components/ui/state-panel";
import { usePatient } from "@/lib/hooks/use-patient";
import type { DoctorBrief } from "@/lib/types";

export default function BriefPage() {
  const { patient, ready } = usePatient();
  const [brief, setBrief] = useState<DoctorBrief | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    const pid = patient?.id;
    if (!pid) {
      setLoading(false);
      return;
    }
    getBrief(pid)
      .then(setBrief)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load brief"))
      .finally(() => setLoading(false));
  }, [patient?.id, ready]);

  if (!ready || loading) {
    return <BriefSkeleton />;
  }

  if (!patient) {
    return (
      <div className="px-5 py-10 text-center">
        <p className="text-text-muted">No patient loaded.</p>
        <Link href="/" className="mt-4 inline-block text-primary underline">
          Go to home
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="px-5 py-8">
        <ErrorPanel title="Couldn't load brief" message={error} retryable onRetry={() => window.location.reload()} />
        <Link href="/upload" className="mt-4 block text-center text-sm font-semibold text-primary">
          Upload a document
        </Link>
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="px-5 py-8">
        <ErrorPanel
          title="No brief yet"
          message="Upload a prescription or lab report to generate your doctor brief."
        />
        <Link href="/upload" className="mt-4 block text-center text-sm font-semibold text-primary">
          Upload a document
        </Link>
      </div>
    );
  }

  return <BriefView brief={brief} patientName={patient.displayName} />;
}
