"use client";

import Link from "next/link";
import { ShareBriefCard } from "@/components/brief/share-brief-card";
import { ScreenHeader } from "@/components/ui/screen-header";
import { BackLink } from "@/components/ui/back-link";
import { usePatient } from "@/lib/hooks/use-patient";

export default function SharePage() {
  const { patient, ready } = usePatient();

  if (!ready) {
    return <p className="p-8 text-center text-sm text-text-faint">Loading…</p>;
  }

  if (!patient?.id) {
    return (
      <div className="px-5 pb-24 pt-5 text-center">
        <p className="text-sm text-text-muted">Sign in to share your doctor brief.</p>
        <Link href="/login" className="mt-3 inline-block text-sm font-semibold text-primary">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="px-[18px] pb-24 pt-5">
      <BackLink href="/brief" label="Back to brief" />
      <ScreenHeader
        title="Show this to your doctor"
        subtitle="Scan the QR or send the link — no app needed on their side."
      />
      <ShareBriefCard patientId={patient.id} patientName={patient.displayName} />
    </div>
  );
}
