"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FolderHeart, Home, Stethoscope, UserRound } from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useLocale } from "@/lib/hooks/use-locale";
import { SaathiAvatar } from "@/components/characters/saathi-avatar";
import { hasSaathiUnread } from "@/lib/saathi-history";

export function BottomNav() {
  const pathname = usePathname();
  const { t } = useLocale();
  const [unread, setUnread] = useState(false);

  useEffect(() => {
    const sync = () => setUnread(hasSaathiUnread());
    sync();
    window.addEventListener("saathi-unread", sync);
    return () => window.removeEventListener("saathi-unread", sync);
  }, []);

  // Home(Today) · Records · ❤Saathi(center) · Care · Me
  const sideTabs = [
    {
      href: "/",
      label: t("nav.today"),
      icon: Home,
      match: (p: string) =>
        p === "/" ||
        p.startsWith("/upload") ||
        p.startsWith("/progress") ||
        p.startsWith("/summary") ||
        p.startsWith("/brief"),
    },
    {
      href: "/memory",
      label: t("nav.records"),
      icon: FolderHeart,
      match: (p: string) =>
        p.startsWith("/memory") || p.startsWith("/vitals") || p.startsWith("/timeline"),
    },
  ];

  const endTabs = [
    {
      href: "/appointments",
      label: t("nav.care"),
      icon: Stethoscope,
      match: (p: string) =>
        p.startsWith("/appointments") || p.startsWith("/doctors") || p.startsWith("/triage"),
    },
    {
      href: "/profile",
      label: t("nav.me"),
      icon: UserRound,
      match: (p: string) =>
        p.startsWith("/profile") || p.startsWith("/share") || p.startsWith("/settings"),
    },
  ];

  const saathiActive = pathname.startsWith("/chat");

  const Tab = ({
    href,
    label,
    icon: Icon,
    match,
  }: {
    href: string;
    label: string;
    icon: typeof Home;
    match: (p: string) => boolean;
  }) => {
    const active = match(pathname);
    const color = active ? "text-primary" : "text-[#A79F92]";
    return (
      <Link
        href={href}
        className="flex min-h-[56px] flex-1 flex-col items-center justify-center gap-0.5 py-2"
      >
        <Icon className={cn("h-[22px] w-[22px]", color)} strokeWidth={active ? 2.1 : 1.8} aria-hidden />
        <span className={cn("text-[11px] font-semibold leading-tight", color)}>{label}</span>
      </Link>
    );
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-surface-raised pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto flex max-w-lg items-end">
        {sideTabs.map((tab) => (
          <Tab key={tab.href} {...tab} />
        ))}

        {/* Saathi — raised coral center */}
        <Link
          href="/chat"
          className="flex flex-1 flex-col items-center justify-end"
          aria-label={t("nav.saathi")}
        >
          <div className="relative -mt-6">
            <div
              className={cn(
                "flex h-14 w-14 items-center justify-center rounded-full border-4 border-surface-raised shadow-[0_6px_16px_rgba(244,121,91,0.4)]",
                saathiActive ? "bg-saathi-deep" : "bg-saathi",
              )}
            >
              <SaathiAvatar state={saathiActive ? "happy" : "idle"} size={40} label={null} />
            </div>
            {unread && (
              <span className="absolute -right-0.5 -top-0.5 h-3.5 w-3.5 rounded-full border-2 border-surface-raised bg-marigold" />
            )}
          </div>
          <span
            className={cn(
              "mb-1 mt-0.5 text-[11px] font-semibold leading-tight",
              saathiActive ? "text-saathi-deep" : "text-saathi",
            )}
          >
            {t("nav.saathi")}
          </span>
        </Link>

        {endTabs.map((tab) => (
          <Tab key={tab.href} {...tab} />
        ))}
      </div>
    </nav>
  );
}
