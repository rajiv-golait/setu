import { DoctorShell } from "@/components/layout/role-shells";
import DoctorDashboard from "./dashboard-client";

export default function DoctorHomePage() {
  return (
    <DoctorShell>
      <DoctorDashboard />
    </DoctorShell>
  );
}
