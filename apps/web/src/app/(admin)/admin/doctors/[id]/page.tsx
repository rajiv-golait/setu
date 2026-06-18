"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { AdminShell } from "@/components/layout/role-shells";
import { BackLink } from "@/components/ui/back-link";
import { PageHeader } from "@/components/ui/page-header";
import { WarmCard } from "@/components/ui/warm-card";
import {
  getAdminProvider,
  listAdminProviderCredentials,
  verifyAdminProvider,
} from "@/lib/api";
import type { AdminProviderRecord } from "@/lib/types";

export default function AdminDoctorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [doctor, setDoctor] = useState<AdminProviderRecord | null>(null);
  const [creds, setCreds] = useState<
    Array<{ id: string; doc_type: string; status: string; created_at: string }>
  >([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [d, c] = await Promise.all([
        getAdminProvider(id),
        listAdminProviderCredentials(id),
      ]);
      setDoctor(d);
      setCreds(c);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load doctor");
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const setStatus = async (status: string) => {
    await verifyAdminProvider(id, status);
    await load();
  };

  return (
    <AdminShell>
      <BackLink href="/admin/doctors" label="All doctors" />
      {!doctor ? (
        <p className="mt-4 text-sm text-text-muted">{error ?? "Loading…"}</p>
      ) : (
        <>
          <PageHeader
            title={doctor.display_name || "Doctor"}
            subtitle={
              [doctor.specialty, doctor.facility].filter(Boolean).join(" · ") ||
              doctor.phone ||
              undefined
            }
          />
          <p className="mt-1 text-sm capitalize">Status: {doctor.verification_status ?? "pending"}</p>
          <div className="mt-4 flex flex-wrap gap-3">
            {doctor.verification_status !== "approved" && (
              <button
                type="button"
                onClick={() => setStatus("approved")}
                className="text-sm font-semibold text-success"
              >
                Approve
              </button>
            )}
            {doctor.verification_status === "approved" && (
              <button
                type="button"
                onClick={() => setStatus("suspended")}
                className="text-sm font-semibold text-warning"
              >
                Suspend
              </button>
            )}
          </div>

          <h2 className="mt-8 text-sm font-semibold uppercase tracking-wide text-text-muted">
            Credentials
          </h2>
          {creds.length === 0 ? (
            <p className="mt-2 text-sm text-text-muted">No documents uploaded.</p>
          ) : (
            <ul className="mt-2 space-y-2">
              {creds.map((c) => (
                <li key={c.id}>
                  <WarmCard className="text-sm">
                    <span className="font-semibold">{c.doc_type}</span>
                    <span className="ml-2 capitalize text-text-muted">{c.status}</span>
                    <span className="ml-2 text-xs text-text-faint">
                      {new Date(c.created_at).toLocaleDateString("en-IN")}
                    </span>
                  </WarmCard>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </AdminShell>
  );
}
