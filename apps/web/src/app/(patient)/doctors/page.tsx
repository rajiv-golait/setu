"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { searchProviders } from "@/lib/api";
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
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <h1 className="text-[23px] font-semibold">Find a specialist</h1>
      <input
        value={specialty}
        onChange={(e) => setSpecialty(e.target.value)}
        placeholder="Search specialty…"
        className="mt-4 w-full rounded-card border border-border px-4 py-3"
      />
      <div className="mt-6 space-y-3">
        {doctors.map((d) => (
          <Link
            key={d.id}
            href={`/doctors/${d.id}`}
            className="block rounded-card border border-border bg-surface-raised p-4 shadow-card"
          >
            <p className="font-semibold">{d.display_name ?? "Doctor"}</p>
            <p className="text-sm text-text-muted">{d.specialty}</p>
            {d.location && <p className="text-xs text-text-faint">{d.location}</p>}
          </Link>
        ))}
        {doctors.length === 0 && (
          <p className="text-sm text-text-muted">No verified doctors match your search.</p>
        )}
      </div>
    </div>
  );
}
