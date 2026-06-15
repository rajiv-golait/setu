"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getBrief } from "@/lib/api";
import { BriefView } from "@/components/brief/brief-view";
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

  if (error || !brief) {
    return (
      <div className="px-5 py-10 text-center">
        <p className="text-text-muted">{error ?? "No brief yet. Upload a document first."}</p>
        <Link href="/" className="mt-4 inline-block text-primary underline">
          Back to home
        </Link>
      </div>
    );
  }

  return <BriefView brief={brief} patientName={patient.displayName} />;
}

function BriefSkeleton() {
  return (
    <div className="animate-pulse px-[18px] py-[18px]">
      <div className="h-32 rounded-hero bg-[#E8E8E2]" />
      <div className="mt-4 h-20 rounded-card bg-[#E8E8E2]" />
      <div className="mt-3 h-20 rounded-card bg-[#E8E8E2]" />
      <div className="mt-3 h-20 rounded-card bg-[#E8E8E2]" />
    </div>
  );
}
