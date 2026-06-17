"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";
import { roleFromMetadata, type UserRole } from "@/lib/auth/role";

export function useUserRole(): { role: UserRole; loading: boolean } {
  const [role, setRole] = useState<UserRole>("patient");
  const [loading, setLoading] = useState(SUPABASE_ENABLED);

  useEffect(() => {
    if (!SUPABASE_ENABLED) {
      setLoading(false);
      return;
    }
    const supabase = createClient();
    if (!supabase) {
      setLoading(false);
      return;
    }
    supabase.auth.getUser().then(({ data: { user } }) => {
      setRole(roleFromMetadata(user?.app_metadata as Record<string, unknown> | undefined));
      setLoading(false);
    });
  }, []);

  return { role, loading };
}

export function DoctorShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { role, loading } = useUserRole();

  if (loading) {
    return <div className="p-8 text-center text-sm text-text-faint">Loading…</div>;
  }

  if (SUPABASE_ENABLED && role !== "provider" && role !== "admin") {
    return (
      <div className="mx-auto max-w-lg p-8 text-center">
        <p className="text-text-muted">Provider access required.</p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-primary">
          Go to patient app
        </Link>
      </div>
    );
  }

  const tabs = [
    { href: "/doctor", label: "Dashboard" },
    { href: "/doctor/appointments", label: "Appointments" },
    { href: "/doctor/settings", label: "Settings" },
  ];

  return (
    <div className="mx-auto min-h-screen max-w-4xl bg-surface">
      <header className="sticky top-0 z-30 border-b border-border bg-surface-raised px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-white">
            S
          </span>
          <span className="font-semibold text-[#3D4A42]">Setu · Doctor</span>
        </div>
        <nav className="mt-3 flex gap-4 overflow-x-auto">
          {tabs.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`whitespace-nowrap pb-1 text-sm font-semibold ${
                pathname === href || (href !== "/doctor" && pathname.startsWith(href))
                  ? "border-b-2 border-primary text-primary"
                  : "text-text-muted"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="px-4 py-6">{children}</main>
    </div>
  );
}

export function WorkerShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { role, loading } = useUserRole();

  if (loading) {
    return <div className="p-8 text-center text-sm text-text-faint">Loading…</div>;
  }

  if (SUPABASE_ENABLED && role !== "health_worker" && role !== "admin") {
    return (
      <div className="mx-auto max-w-lg p-8 text-center">
        <p className="text-text-muted">Health worker access required.</p>
        <Link href="/" className="mt-4 inline-block text-sm font-semibold text-primary">
          Go to patient app
        </Link>
      </div>
    );
  }

  const tabs = [
    { href: "/worker", label: "Patients" },
    { href: "/worker/register", label: "Register" },
    { href: "/worker/follow-ups", label: "Follow-ups" },
  ];

  return (
    <div className="mx-auto min-h-screen max-w-lg bg-surface">
      <header className="border-b border-border bg-[#EEF4F0] px-4 py-3">
        <p className="text-xs font-bold uppercase tracking-wide text-primary">ASHA / PHC</p>
        <nav className="mt-2 flex gap-3">
          {tabs.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`text-sm font-semibold ${
                pathname === href ? "text-primary" : "text-text-muted"
              }`}
            >
              {label}
            </Link>
          ))}
        </nav>
      </header>
      <main className="px-4 py-5 pb-8">{children}</main>
    </div>
  );
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const { role, loading } = useUserRole();

  if (loading) {
    return <div className="p-8 text-center text-sm text-text-faint">Loading…</div>;
  }

  if (SUPABASE_ENABLED && role !== "admin") {
    return (
      <div className="mx-auto max-w-lg p-8 text-center">
        <p className="text-text-muted">Admin access required.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto min-h-screen max-w-5xl bg-surface px-4 py-6">
      <h1 className="text-xl font-semibold">Setu Analytics</h1>
      {children}
    </div>
  );
}
