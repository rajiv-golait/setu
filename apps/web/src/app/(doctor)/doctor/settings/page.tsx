"use client";

import { useEffect, useState } from "react";
import { DoctorShell } from "@/components/layout/role-shells";
import { PrimaryButton } from "@/components/ui/buttons";
import { getProviderMe, updateProviderMe } from "@/lib/api";
import type { ProviderRecord } from "@/lib/types";

export default function DoctorSettingsPage() {
  const [provider, setProvider] = useState<ProviderRecord | null>(null);
  const [name, setName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [facility, setFacility] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getProviderMe().then((p) => {
      setProvider(p);
      setName(p.display_name ?? "");
      setSpecialty(p.specialty ?? "");
      setFacility(p.facility ?? "");
    });
  }, []);

  const save = async () => {
    const updated = await updateProviderMe({
      display_name: name,
      specialty,
      facility,
    });
    setProvider(updated);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <DoctorShell>
      <h1 className="text-xl font-semibold">Profile</h1>
      <div className="mt-6 space-y-4 max-w-md">
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
        <PrimaryButton onClick={save}>Save</PrimaryButton>
        {saved && <p className="text-sm text-success">Saved.</p>}
        {provider && (
          <p className="text-xs text-text-faint">Provider ID: {provider.id}</p>
        )}
      </div>
    </DoctorShell>
  );
}
