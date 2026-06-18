"use client";

import { useEffect, useState } from "react";
import { searchProviders } from "@/lib/api";
import { ScreenHeader } from "@/components/ui/screen-header";
import { DataTable, DataRow } from "@/components/ui/data-table";
import type { ProviderRecord } from "@/lib/types";

export default function DoctorsDirectoryPage() {
  const [doctors, setDoctors] = useState<ProviderRecord[]>([]);
  const [specialty, setSpecialty] = useState("");

  useEffect(() => {
    searchProviders(specialty ? { specialty } : undefined)
      .then(setDoctors)
      .catch(() => setDoctors([]));
  }, [specialty]);

  return (
    <div className="px-5 pb-24 pt-5">
      <ScreenHeader
        title="Find a specialist"
        subtitle="Search by specialty and book a visit with your brief attached."
      />
      <input
        value={specialty}
        onChange={(e) => setSpecialty(e.target.value)}
        placeholder="Search specialty…"
        className="sticky top-14 z-10 mt-4 w-full rounded-card border border-border bg-surface px-4 py-3 shadow-sm"
      />
      {doctors.length === 0 ? (
        <p className="mt-6 text-sm text-text-muted">No verified doctors match your search.</p>
      ) : (
        <DataTable className="mt-6">
          {doctors.map((d) => (
            <DataRow key={d.id} onClick={() => { window.location.href = `/doctors/${d.id}`; }}>
              <div>
                <p className="font-semibold">{d.display_name ?? "Doctor"}</p>
                <p className="text-sm text-text-muted">{d.specialty}</p>
                {d.facility && <p className="text-xs text-text-faint">{d.facility}</p>}
              </div>
            </DataRow>
          ))}
        </DataTable>
      )}
    </div>
  );
}
