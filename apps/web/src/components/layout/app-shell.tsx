"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { BottomNav } from "./bottom-nav";
import { NotificationBell } from "@/components/ui/notification-bell";
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

  useEffect(() => {
    if (!SUPABASE_ENABLED) return;
    if (pathname === "/onboarding" || pathname === "/login") return;
    if (typeof window !== "undefined" && !localStorage.getItem("setu_onboarded")) {
      router.replace("/onboarding");
    }
  }, [pathname, router]);

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
