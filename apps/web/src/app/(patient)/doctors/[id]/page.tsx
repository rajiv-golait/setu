"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PrimaryButton } from "@/components/ui/buttons";
import { ScreenHeader } from "@/components/ui/screen-header";
import { SectionHeading } from "@/components/ui/section-heading";
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
    <div className="px-5 pb-24 pt-5">
      <ScreenHeader
        mode="toolbar"
        backHref="/doctors"
        backLabel="Directory"
        title={doctor.display_name ?? "Doctor"}
      />
      {doctor.specialty && <p className="mt-1 text-sm text-text-muted">{doctor.specialty}</p>}
      {doctor.bio && <p className="text-sm">{doctor.bio}</p>}
      {doctor.consultation_fee != null && (
        <p className="mt-2 text-sm font-semibold">Fee: ₹{doctor.consultation_fee}</p>
      )}

      <SectionHeading title="Available slots" className="mt-8" />
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
    </div>
  );
}
