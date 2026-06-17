"use client";

import type { VitalReading, VitalType } from "@/lib/types";
import { LabSparkline } from "@/components/ui/sparkline";

export function VitalTrendChart({
  readings,
  vitalType,
}: {
  readings: VitalReading[];
  vitalType: VitalType;
}) {
  const filtered = readings
    .filter((r) => r.vital_type === vitalType)
    .sort((a, b) => a.measured_at.localeCompare(b.measured_at));

  const values = filtered.map((r) => {
    const v = r.value;
    if (vitalType === "blood_pressure" && typeof v.systolic === "number") return v.systolic as number;
    if (vitalType === "blood_sugar" && typeof v.fasting === "number") return v.fasting as number;
    if (vitalType === "spo2" && typeof v.percent === "number") return v.percent as number;
    if (vitalType === "heart_rate" && typeof v.bpm === "number") return v.bpm as number;
    return 0;
  });

  if (values.length < 2) return null;

  return (
    <div className="mt-2 flex justify-center">
      <LabSparkline points={values} />
    </div>
  );
}

export function formatVitalValue(reading: VitalReading): string {
  const v = reading.value;
  switch (reading.vital_type) {
    case "blood_pressure":
      return `${v.systolic}/${v.diastolic} ${reading.unit}`;
    case "blood_sugar":
      return `${v.fasting ?? v.random} ${reading.unit}`;
    case "spo2":
      return `${v.percent}%`;
    case "heart_rate":
      return `${v.bpm} bpm`;
    default:
      return JSON.stringify(v);
  }
}
