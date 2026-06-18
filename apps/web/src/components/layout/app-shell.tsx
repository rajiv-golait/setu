"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { BottomNav } from "./bottom-nav";
import { NotificationBell } from "@/components/ui/notification-bell";
import { usePatient } from "@/lib/hooks/use-patient";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";

export function AppShell({
  children,
  hideNav = false,
}: {
  children: React.ReactNode;
  hideNav?: boolean;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const { patient, ready } = usePatient();

  useEffect(() => {
    if (!SUPABASE_ENABLED || !ready) return;
    if (pathname === "/onboarding" || pathname === "/login") return;
    if (patient && !patient.onboardingCompleted) {
      router.replace("/onboarding");
    }
  }, [pathname, patient, ready, router]);

  return (
    <div className="mx-auto min-h-screen max-w-lg bg-surface">
      {!hideNav && (
        <div className="flex justify-end px-4 pt-3">
          <NotificationBell />
        </div>
      )}
      <main className={hideNav ? "pb-6" : "pb-24"}>{children}</main>
      {!hideNav && <BottomNav />}
    </div>
  );
}
