"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AdminShell } from "@/components/layout/role-shells";
import { PrimaryButton } from "@/components/ui/buttons";
import { grantAdminProvider, listAdminProviders, revokeAdminProvider, verifyAdminProvider } from "@/lib/api";
import type { AdminProviderRecord } from "@/lib/types";

export default function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<AdminProviderRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [phone, setPhone] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [facility, setFacility] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDoctors(await listAdminProviders());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load doctors");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onGrant = async () => {
    setSaving(true);
    setError(null);
    try {
      await grantAdminProvider({
        phone,
        display_name: displayName || undefined,
        specialty: specialty || undefined,
        facility: facility || undefined,
      });
      setPhone("");
      setDisplayName("");
      setSpecialty("");
      setFacility("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not add doctor");
    } finally {
      setSaving(false);
    }
  };

  const onVerify = async (id: string, status: string) => {
    setError(null);
    try {
      await verifyAdminProvider(id, status);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update verification");
    }
  };

  const statusBadge = (status?: string) => {
    const s = status ?? "pending";
    const colors =
      s === "approved"
        ? "text-success border-success-border bg-success-bg"
        : s === "suspended"
          ? "text-danger border-danger-border bg-danger-bg"
          : "text-warning border-border bg-surface";
    return (
      <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold capitalize ${colors}`}>
        {s}
      </span>
    );
  };

  const onRevoke = async (id: string) => {
    if (!confirm("Remove doctor access? They will sign in as a patient.")) return;
    setError(null);
    try {
      await revokeAdminProvider(id);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not remove doctor");
    }
  };

  return (
    <AdminShell>
      <p className="text-sm text-text-muted">
        Add a doctor by mobile number. They sign in at{" "}
        <span className="font-semibold text-primary">/doctor/login</span> after you grant access.
      </p>

      <div className="mt-6 rounded-card border border-border bg-surface-raised p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">Add doctor</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="block sm:col-span-2">
            <span className="text-sm font-semibold">Mobile number *</span>
            <input
              type="tel"
              inputMode="tel"
              placeholder="9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="mt-1 w-full rounded-card border border-border bg-surface px-3 py-2 text-base"
            />
          </label>
          <label className="block">
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
            <input
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              placeholder="dermatology"
              className="mt-1 w-full rounded-card border border-border bg-surface px-3 py-2"
            />
          </label>
          <label className="block sm:col-span-2">
            <span className="text-sm font-semibold">Facility</span>
            <input
              value={facility}
              onChange={(e) => setFacility(e.target.value)}
              placeholder="District hospital"
              className="mt-1 w-full rounded-card border border-border bg-surface px-3 py-2"
            />
          </label>
        </div>
        <PrimaryButton
          className="mt-4"
          disabled={saving || phone.replace(/\D/g, "").length < 10}
          onClick={onGrant}
        >
          {saving ? "Saving…" : "Grant doctor access"}
        </PrimaryButton>
      </div>

      {error && <p className="mt-4 text-sm text-danger">{error}</p>}

      <div className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-text-muted">
          Registered doctors
        </h2>
        {loading ? (
          <p className="mt-3 text-sm text-text-faint">Loading…</p>
        ) : doctors.length === 0 ? (
          <p className="mt-3 text-sm text-text-muted">No doctors yet.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {doctors.map((d) => (
              <li
                key={d.id}
                className="flex flex-wrap items-start justify-between gap-3 rounded-card border border-border bg-surface-raised p-4"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold">{d.display_name || "Doctor"}</p>
                    {statusBadge(d.verification_status)}
                  </div>
                  <p className="text-sm text-text-muted">{d.phone || d.supabase_user_id}</p>
                  {(d.specialty || d.facility) && (
                    <p className="mt-1 text-sm text-text-muted">
                      {[d.specialty, d.facility].filter(Boolean).join(" · ")}
                    </p>
                  )}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <Link href={`/admin/doctors/${d.id}`} className="text-sm font-semibold text-primary">
                    Review →
                  </Link>
                  {d.verification_status !== "approved" && (
                    <button
                      type="button"
                      onClick={() => onVerify(d.id, "approved")}
                      className="text-sm font-semibold text-success"
                    >
                      Approve
                    </button>
                  )}
                  {d.verification_status === "approved" && (
                    <button
                      type="button"
                      onClick={() => onVerify(d.id, "suspended")}
                      className="text-sm font-semibold text-warning"
                    >
                      Suspend
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => onRevoke(d.id)}
                    className="text-sm font-semibold text-danger"
                  >
                    Revoke
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AdminShell>
  );
}
