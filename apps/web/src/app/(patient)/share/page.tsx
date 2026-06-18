"use client";

import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { ShareBriefCard } from "@/components/brief/share-brief-card";
import { usePatient } from "@/lib/hooks/use-patient";

export default function SharePage() {
  const { patient, ready } = usePatient();

  if (!ready) {
    return <p className="p-8 text-center text-sm text-text-faint">Loading…</p>;
  }

  if (!patient?.id) {
    return (
      <div className="animate-setu-fade px-5 pb-24 pt-5 text-center">
        <p className="text-sm text-text-muted">Sign in to share your doctor brief.</p>
        <Link href="/login" className="mt-3 inline-block text-sm font-semibold text-primary">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="animate-setu-fade px-[18px] pb-24 pt-5">
      <Link href="/brief" className="mb-4 inline-flex items-center gap-1 text-sm font-semibold text-primary">
        <ChevronLeft className="h-4 w-4" aria-hidden />
        Back to brief
      </Link>
      <div className="mb-5 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.08em] text-primary-light">
          Share with doctor
        </p>
        <h1 className="mt-1 text-[22px] font-semibold tracking-tight">Show this to your doctor</h1>
        <p className="mt-1 text-sm text-text-muted">Scan the QR or send the link — no app needed.</p>
      </div>

      <ShareBriefCard patientId={patient.id} patientName={patient.displayName} />
    </div>
  );
}
