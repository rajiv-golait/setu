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
  const immersive = hideNav || pathname.startsWith("/chat");

  useEffect(() => {
    if (!SUPABASE_ENABLED || !ready) return;
    if (pathname === "/onboarding" || pathname === "/login") return;
    if (patient && !patient.onboardingCompleted) {
      router.replace("/onboarding");
    }
  }, [pathname, patient, ready, router]);

  return (
    <div
      className={
        immersive
          ? "mx-auto flex h-dvh max-w-lg flex-col bg-surface"
          : "mx-auto min-h-screen max-w-lg bg-surface"
      }
    >
      {!hideNav && !immersive && (
        <header className="flex items-center justify-between border-b border-border/60 bg-surface-raised/80 px-4 py-2.5">
          <span className="font-display text-sm font-semibold text-primary">Setu</span>
          <NotificationBell />
        </header>
      )}
      <main
        className={
          immersive ? "flex min-h-0 flex-1 flex-col" : hideNav ? "pb-6" : "pb-24"
        }
      >
        {children}
      </main>
      {!hideNav && <BottomNav />}
    </div>
  );
}
