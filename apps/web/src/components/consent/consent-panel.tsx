"use client";

import { useState } from "react";
import { PrimaryButton } from "@/components/ui/buttons";
import { grantConsent } from "@/lib/api";
import { consentText, hasLocalConsent, markLocalConsent } from "@/lib/consent";

export function ConsentPanel({
  patientId,
  lang,
  onGranted,
}: {
  patientId: string;
  lang: string;
  onGranted: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (hasLocalConsent(patientId)) {
    return null;
  }

  const accept = async () => {
    setLoading(true);
    setError(null);
    try {
      await grantConsent({ patient_id: patientId, lang });
      markLocalConsent(patientId);
      onGranted();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not record consent");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-card border border-border bg-surface-raised p-5 shadow-card">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary-light">Consent</p>
      <p className="mt-3 text-sm leading-relaxed text-text">{consentText(lang)}</p>
      <p className="mt-2 text-xs text-text-faint">You can delete your data anytime from settings.</p>
      {error && <p className="mt-2 text-sm text-danger">{error}</p>}
      <PrimaryButton className="mt-4" disabled={loading} onClick={accept}>
        {loading ? "Saving…" : "I agree — continue"}
      </PrimaryButton>
    </div>
  );
}
