"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { SUPABASE_ENABLED } from "@/lib/supabase/config";
import { roleFromMetadata, type UserRole } from "@/lib/auth/role";
import { getAuthMe, getProviderDashboard } from "@/lib/api";
import { NotificationBell } from "@/components/ui/notification-bell";
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
      setRole(
        roleFromMetadata(
          user?.app_metadata as Record<string, unknown> | undefined,
          user?.email,
        ),
      );
      setLoading(false);
    });
  }, []);

  return { role, loading };
}

export function DoctorShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { role, loading } = useUserRole();
  const [pendingCount, setPendingCount] = useState(0);

  useEffect(() => {
    if (!SUPABASE_ENABLED || loading || role !== "provider") return;
    getAuthMe()
      .then((me) => {
        if (
          me.verification_status !== "approved" &&
          !pathname.startsWith("/doctor/pending") &&
          !pathname.startsWith("/doctor/onboarding") &&
          !pathname.startsWith("/doctor/settings")
        ) {
          router.replace("/doctor/pending");
        }
      })
      .catch(() => undefined);
    getProviderDashboard()
      .then((d) => setPendingCount(d.pending_requests))
      .catch(() => setPendingCount(0));
  }, [loading, role, pathname, router]);

  const signOut = async () => {
    const supabase = createClient();
    if (supabase) await supabase.auth.signOut();
    router.replace("/doctor/login");
  };

  if (loading) {
    return <div className="p-8 text-center text-sm text-text-faint">Loading…</div>;
  }

  if (SUPABASE_ENABLED && role !== "provider" && role !== "admin") {
    return (
      <div className="mx-auto max-w-lg p-8 text-center">
        <p className="text-text-muted">Provider access required.</p>
        <Link href="/doctor/login" className="mt-4 inline-block text-sm font-semibold text-primary">
          Doctor sign in
        </Link>
      </div>
    );
  }

  const tabs = [
    { href: "/doctor", label: "Dashboard" },
    { href: "/doctor/appointments", label: "Appointments", badge: pendingCount },
    { href: "/doctor/patients", label: "Patients" },
    { href: "/doctor/consultations", label: "Consultations" },
    { href: "/doctor/calendar", label: "Calendar" },
    { href: "/doctor/settings", label: "Settings" },
  ];

  return (
    <div className="mx-auto min-h-screen max-w-5xl bg-surface">
      <header className="sticky top-0 z-30 border-b border-border bg-surface-raised px-4 py-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-white">
              S
            </span>
            <span className="font-semibold text-[#3D4A42]">Setu · Doctor</span>
          </div>
          <div className="flex items-center gap-3">
            <NotificationBell />
            <button
              type="button"
              onClick={() => void signOut()}
              className="text-sm font-semibold text-text-muted hover:text-primary"
            >
              Sign out
            </button>
          </div>
        </div>
        <nav className="mt-3 flex gap-4 overflow-x-auto">
          {tabs.map(({ href, label, badge }) => (
            <Link
              key={href}
              href={href}
              className={`relative whitespace-nowrap pb-1 text-sm font-semibold ${
                pathname === href || (href !== "/doctor" && pathname.startsWith(href))
                  ? "border-b-2 border-primary text-primary"
                  : "text-text-muted"
              }`}
            >
              {label}
              {badge != null && badge > 0 && (
                <span className="ml-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-warning px-1 text-[10px] font-bold text-white">
                  {badge > 9 ? "9+" : badge}
                </span>
              )}
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
  const pathname = usePathname();
  const { role, loading } = useUserRole();

  if (loading) {
    return <div className="p-8 text-center text-sm text-text-faint">Loading…</div>;
  }

  if (SUPABASE_ENABLED && role !== "admin") {
    return (
      <div className="mx-auto max-w-lg p-8 text-center">
        <p className="text-text-muted">Admin access required.</p>
        <Link href="/admin/login" className="mt-4 inline-block text-sm font-semibold text-primary">
          Admin sign in
        </Link>
      </div>
    );
  }

  const tabs = [
    { href: "/admin", label: "Overview" },
    { href: "/admin/users", label: "Users" },
    { href: "/admin/doctors", label: "Doctors" },
    { href: "/admin/appointments", label: "Appointments" },
    { href: "/admin/patients", label: "Patients" },
    { href: "/admin/support", label: "Support" },
  ];

  return (
    <div className="mx-auto min-h-screen max-w-5xl bg-surface">
      <header className="border-b border-border bg-surface-raised px-4 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold">Setu Admin</h1>
          <NotificationBell />
        </div>
        <nav className="mt-3 flex gap-4 overflow-x-auto">
          {tabs.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`whitespace-nowrap pb-1 text-sm font-semibold ${
                pathname === href || (href !== "/admin" && pathname.startsWith(href))
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
