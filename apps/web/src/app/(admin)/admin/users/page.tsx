"use client";

import { useState } from "react";
import Link from "next/link";
import { AdminShell } from "@/components/layout/role-shells";
import { PrimaryButton } from "@/components/ui/buttons";
import { ScreenHeader } from "@/components/ui/screen-header";
import { WarmCard } from "@/components/ui/warm-card";
import { setAdminUserRole } from "@/lib/api";
import { MEDICAL_SPECIALTIES } from "@/lib/specialties";

type PortalRole = "patient" | "provider";

export default function AdminUsersPage() {
  const [phone, setPhone] = useState("");
  const [role, setRole] = useState<PortalRole>("provider");
  const [displayName, setDisplayName] = useState("");
  const [specialty, setSpecialty] = useState<string>(MEDICAL_SPECIALTIES[0]);
  const [facility, setFacility] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onSave = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await setAdminUserRole({
        phone,
        role,
        display_name: role === "provider" ? displayName || undefined : undefined,
        specialty: role === "provider" ? specialty || undefined : undefined,
        facility: role === "provider" ? facility || undefined : undefined,
      });
      const portal = role === "provider" ? "doctor" : "patient";
      setSuccess(
        `Done. ${res.phone} is now a ${portal}. They sign in with OTP at ${
          role === "provider" ? "/doctor/login" : "/login"
        }.`,
      );
      setPhone("");
      setDisplayName("");
      setSpecialty(MEDICAL_SPECIALTIES[0]);
      setFacility("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update role");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AdminShell>
      <ScreenHeader
        title="User roles"
        subtitle="Set whether a phone number uses the patient or doctor app. They still sign in with OTP."
      />

      <div className="mt-4 grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div>
      <WarmCard variant="inset">
        <h2 className="text-label text-text-muted">Set portal role</h2>

        <label className="mt-4 block">
          <span className="text-sm font-semibold">Mobile number</span>
          <input
            type="tel"
            inputMode="tel"
            placeholder="10-digit number used for OTP login"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="mt-1 w-full rounded-card border border-border bg-surface px-3 py-2 text-base"
          />
        </label>

        <div className="mt-4 flex flex-wrap gap-2">
          {(
            [
              ["patient", "Patient app"],
              ["provider", "Doctor app"],
            ] as const
          ).map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setRole(id)}
              className={`rounded-full px-3 py-1.5 text-[13px] font-semibold ${
                role === id ? "bg-primary text-white" : "border border-border bg-surface text-text-muted"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {role === "provider" && (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="block sm:col-span-2">
              <span className="text-sm font-semibold">Display name</span>
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Dr. Sharma"
                className="mt-1 w-full rounded-card border border-border bg-surface px-3 py-2"
              />
            </label>
            <label className="block">
              <span className="text-sm font-semibold">Specialty</span>
              <select
                value={specialty}
                onChange={(e) => setSpecialty(e.target.value)}
                className="mt-1 w-full rounded-card border border-border bg-surface px-3 py-2"
              >
                {MEDICAL_SPECIALTIES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-sm font-semibold">Facility</span>
              <input
                value={facility}
                onChange={(e) => setFacility(e.target.value)}
                placeholder="District hospital"
                className="mt-1 w-full rounded-card border border-border bg-surface px-3 py-2"
              />
            </label>
          </div>
        )}

        <PrimaryButton
          className="mt-4"
          disabled={saving || phone.replace(/\D/g, "").length < 10}
          onClick={onSave}
        >
          {saving ? "Saving…" : "Save role"}
        </PrimaryButton>
      </WarmCard>

      {error && <p className="mt-4 text-sm text-danger">{error}</p>}
      {success && <p className="mt-4 text-sm text-success">{success}</p>}
        </div>

        <aside className="rounded-card border border-border bg-surface p-4 text-sm text-text-muted lg:sticky lg:top-24 lg:self-start">
          <p className="font-semibold text-text">Quick test flow</p>
          <ol className="mt-2 list-decimal space-y-1 pl-5">
            <li>Set a number as <strong>Doctor app</strong> here.</li>
            <li>
              Open <Link href="/doctor/login" className="font-semibold text-primary">/doctor/login</Link> and OTP
              sign in with that number.
            </li>
            <li>To switch back, set the same number as <strong>Patient app</strong>.</li>
            <li>
              Patient UI: <Link href="/login" className="font-semibold text-primary">/login</Link>
            </li>
          </ol>
        </aside>
      </div>
    </AdminShell>
  );
}
