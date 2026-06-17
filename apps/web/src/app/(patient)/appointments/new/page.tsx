import { Suspense } from "react";
import NewAppointmentClient from "./new-appointment-client";

export default function NewAppointmentPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-sm text-text-faint">Loading…</div>}>
      <NewAppointmentClient />
    </Suspense>
  );
}
