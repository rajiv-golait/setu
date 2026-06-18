"use client";

import { useEffect, useState } from "react";
import { PrimaryButton } from "@/components/ui/buttons";
import { ScreenHeader } from "@/components/ui/screen-header";
import { WarmCard } from "@/components/ui/warm-card";
import { getProviderMe, updateProviderMe, uploadProviderCredential } from "@/lib/api";
import type { ProviderRecord } from "@/lib/types";

export default function DoctorSettingsPage() {
  const [provider, setProvider] = useState<ProviderRecord | null>(null);
  const [name, setName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [facility, setFacility] = useState("");
  const [location, setLocation] = useState("");
  const [bio, setBio] = useState("");
  const [fee, setFee] = useState("");
  const [saved, setSaved] = useState(false);
  const [credMsg, setCredMsg] = useState<string | null>(null);

  useEffect(() => {
    getProviderMe().then((p) => {
      setProvider(p);
      setName(p.display_name ?? "");
      setSpecialty(p.specialty ?? "");
      setFacility(p.facility ?? "");
      setLocation(p.location ?? "");
      setBio(p.bio ?? "");
      setFee(p.consultation_fee != null ? String(p.consultation_fee) : "");
    });
  }, []);

  const save = async () => {
    const updated = await updateProviderMe({
      display_name: name,
      specialty,
      facility,
      location: location || undefined,
      bio: bio || undefined,
      consultation_fee: fee ? parseInt(fee, 10) : undefined,
    });
    setProvider(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const uploadCred = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setCredMsg(null);
    try {
      const res = await uploadProviderCredential("medical_license", file);
      setCredMsg(`Credential uploaded (${res.status}). Admin will review.`);
    } catch (err) {
      setCredMsg(err instanceof Error ? err.message : "Upload failed");
    }
  };

  return (
    <>
      <ScreenHeader title="Profile" subtitle="Your practice details and credentials." />
      {provider?.verification_status && provider.verification_status !== "approved" && (
        <p className="mt-2 rounded-lg bg-warning/10 px-3 py-2 text-sm text-warning">
          Verification status: {provider.verification_status}. Upload credentials below.
        </p>
      )}
      <WarmCard variant="inset" className="mt-6 max-w-md space-y-4">
        <label className="block text-sm font-semibold">
          Display name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          Specialty
          <input
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          Facility
          <input
            value={facility}
            onChange={(e) => setFacility(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          Location
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          Consultation fee (₹)
          <input
            type="number"
            value={fee}
            onChange={(e) => setFee(e.target.value)}
            className="mt-1 w-full rounded-card border border-border px-4 py-3"
          />
        </label>
        <label className="block text-sm font-semibold">
          Bio
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded-card border border-border px-4 py-3 text-sm"
          />
        </label>
        <PrimaryButton onClick={save}>Save</PrimaryButton>
        {saved && <p className="text-sm text-success">Saved.</p>}

        <div className="mt-8 border-t border-border pt-6">
          <h2 className="text-sm font-semibold">Medical credentials</h2>
          <p className="mt-1 text-sm text-text-muted">
            Upload license or registration for admin verification.
          </p>
          <input type="file" accept="image/*,application/pdf" className="mt-3 text-sm" onChange={uploadCred} />
          {credMsg && <p className="mt-2 text-sm text-text-muted">{credMsg}</p>}
        </div>
      </WarmCard>
    </>
  );
}
