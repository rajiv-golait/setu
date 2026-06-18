"use client";

import { usePathname } from "next/navigation";
import { InstallAppPrompt } from "@/components/pwa/install-app-prompt";

/** Site-wide install banner (patient, doctor, worker shells). */
export function PwaInstallGate() {
  const pathname = usePathname();
  return <InstallAppPrompt pathname={pathname} />;
}
