"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { getProviderPublic, listProviderSlots } from "@/lib/api";
import type { AppointmentSlot, ProviderRecord } from "@/lib/types";

export default function DoctorProfilePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [doctor, setDoctor] = useState<ProviderRecord | null>(null);
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    getProviderPublic(id).then(setDoctor).catch(() => setDoctor(null));
    listProviderSlots(id).then(setSlots).catch(() => setSlots([]));
  }, [id]);

  if (!doctor) {
    return <div className="p-8 text-center text-sm text-text-muted">Loading…</div>;
  }

  return (
    <div className="animate-setu-fade px-5 pb-24 pt-5">
      <h1 className="text-2xl font-semibold">{doctor.display_name}</h1>
      <p className="text-sm text-text-muted">{doctor.specialty}</p>
      {doctor.bio && <p className="mt-3 text-sm">{doctor.bio}</p>}
      {doctor.consultation_fee != null && (
        <p className="mt-2 text-sm font-semibold">Fee: ₹{doctor.consultation_fee}</p>
      )}

      <h2 className="mb-2 mt-8 text-sm font-semibold uppercase text-text-muted">
        Available slots
      </h2>
      <div className="space-y-2">
        {slots.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSelectedSlot(s.id)}
            className={`w-full rounded-card border px-4 py-3 text-left text-sm ${
              selectedSlot === s.id ? "border-primary bg-[#EEF4F0]" : "border-border"
            }`}
          >
            {new Date(s.starts_at).toLocaleString("en-IN")}
          </button>
        ))}
        {slots.length === 0 && (
          <p className="text-sm text-text-muted">No open slots — try another day.</p>
        )}
      </div>

      <PrimaryButton
        className="mt-6"
        disabled={!selectedSlot}
        onClick={() =>
          router.push(
            `/appointments/new?provider_id=${id}&slot_id=${selectedSlot}&specialty=${encodeURIComponent(doctor.specialty ?? "")}`,
          )
        }
      >
        Book consultation
      </PrimaryButton>
      <Link href="/doctors" className="mt-4 block text-center text-sm font-semibold text-primary">
        Back to directory
      </Link>
    </div>
  );
}
