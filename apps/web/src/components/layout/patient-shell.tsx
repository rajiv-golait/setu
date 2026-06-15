"use client";

import { usePathname } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";

const HIDE_NAV = ["/upload", "/progress"];

export function PatientShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const hideNav = HIDE_NAV.some((p) => pathname.startsWith(p));
  return <AppShell hideNav={hideNav}>{children}</AppShell>;
}
