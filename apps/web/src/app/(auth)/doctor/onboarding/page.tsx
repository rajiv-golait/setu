"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { registerProvider, uploadProviderCredential } from "@/lib/api";

const STEPS = ["Profile", "Credentials", "Done"] as const;

export default function DoctorOnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [displayName, setDisplayName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [facility, setFacility] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saveProfile = async () => {
    setBusy(true);
    setError(null);
    try {
      await registerProvider({
        display_name: displayName,
        specialty,
        facility,
      });
      setStep(1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save profile");
    } finally {
      setBusy(false);
    }
  };

  const uploadCred = async () => {
    if (!file) {
      setStep(2);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await uploadProviderCredential("medical_license", file);
      setStep(2);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not upload document");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto min-h-screen max-w-lg px-5 py-10">
      <p className="text-xs font-semibold uppercase tracking-wide text-primary">Doctor onboarding</p>
      <h1 className="mt-1 text-2xl font-semibold">Set up your practice</h1>
      <p className="mt-2 text-sm text-text-muted">
        Step {step + 1} of {STEPS.length}: {STEPS[step]}
      </p>

      {step === 0 && (
        <div className="mt-8 space-y-4">
          <label className="block">
            <span className="text-sm font-semibold">Display name</span>
            <input
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="mt-1 w-full rounded-card border border-border px-4 py-3"
              placeholder="Dr. Sharma"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold">Specialty</span>
            <input
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              className="mt-1 w-full rounded-card border border-border px-4 py-3"
              placeholder="General medicine"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold">Facility</span>
            <input
              value={facility}
              onChange={(e) => setFacility(e.target.value)}
              className="mt-1 w-full rounded-card border border-border px-4 py-3"
              placeholder="District hospital"
            />
          </label>
          <PrimaryButton disabled={busy || !displayName.trim()} onClick={saveProfile}>
            Continue
          </PrimaryButton>
        </div>
      )}

      {step === 1 && (
        <div className="mt-8 space-y-4">
          <p className="text-sm text-text-muted">
            Upload your medical registration or clinic ID (optional for now — admin will verify).
          </p>
          <input
            type="file"
            accept="image/*,application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
          <PrimaryButton disabled={busy} onClick={uploadCred}>
            {file ? "Upload & continue" : "Skip for now"}
          </PrimaryButton>
        </div>
      )}

      {step === 2 && (
        <div className="mt-8">
          <p className="text-sm text-text-muted">
            Your profile is submitted. An admin will approve your account before you can accept
            patients.
          </p>
          <PrimaryButton className="mt-4" onClick={() => router.replace("/doctor/pending")}>
            Go to pending status
          </PrimaryButton>
        </div>
      )}

      {error && <p className="mt-4 text-sm text-danger">{error}</p>}
    </div>
  );
}
