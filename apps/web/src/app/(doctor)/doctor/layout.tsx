import { DoctorShell } from "@/components/layout/role-shells";

export default function DoctorLayout({ children }: { children: React.ReactNode }) {
  return <DoctorShell>{children}</DoctorShell>;
}
