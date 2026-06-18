"use client";

import { useEffect, useState } from "react";
import { AdminShell } from "@/components/layout/role-shells";
import { ScreenHeader } from "@/components/ui/screen-header";
import { DataTable, DataRow } from "@/components/ui/data-table";
import { listAdminAppointments } from "@/lib/api";
import type { Appointment } from "@/lib/types";

const FILTERS = ["", "requested", "accepted", "confirmed", "completed", "cancelled"];

export default function AdminAppointmentsPage() {
  const [filter, setFilter] = useState("");
  const [items, setItems] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listAdminAppointments(filter || undefined)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [filter]);

  return (
    <AdminShell>
      <ScreenHeader title="All appointments" subtitle="Platform-wide visit requests and bookings." />
      <div className="mt-4 flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f || "all"}
            type="button"
            onClick={() => setFilter(f)}
            className={`rounded-full border px-3 py-1 text-sm font-semibold ${
              filter === f ? "border-primary bg-primary text-white" : "border-border"
            }`}
          >
            {f || "All"}
          </button>
        ))}
      </div>
      {loading ? (
        <p className="mt-6 text-sm text-text-faint">Loading…</p>
      ) : items.length === 0 ? (
        <p className="mt-6 text-sm text-text-muted">No appointments.</p>
      ) : (
        <DataTable className="mt-6">
          {items.map((a) => (
            <DataRow key={a.id}>
              <div className="text-sm">
                <p className="font-semibold">{a.specialty}</p>
                <p className="capitalize text-text-muted">Status: {a.status}</p>
                <p className="text-text-muted">
                  Patient {a.patient_id.slice(0, 8)}… · Provider {a.provider_id?.slice(0, 8) ?? "—"}…
                </p>
                {a.scheduled_for && (
                  <p className="text-text-muted">
                    {new Date(a.scheduled_for).toLocaleString("en-IN")}
                  </p>
                )}
              </div>
            </DataRow>
          ))}
        </DataTable>
      )}
    </AdminShell>
  );
}
