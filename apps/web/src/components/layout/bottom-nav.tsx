"use client";

import Link from "next/link";
import {
  BookOpen,
  Calendar,
  Camera,
  LayoutList,
  QrCode,
  Stethoscope,
} from "lucide-react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import { useLocale } from "@/lib/hooks/use-locale";

export function BottomNav() {
  const pathname = usePathname();
  const { t } = useLocale();

  const tabs = [
    { href: "/", label: t("nav.home"), icon: Camera },
    { href: "/summary", label: t("nav.summary"), icon: BookOpen },
    { href: "/triage", label: t("nav.triage"), icon: Stethoscope },
    { href: "/appointments", label: t("nav.appointments"), icon: Calendar },
    { href: "/memory", label: t("nav.memory"), icon: LayoutList },
    { href: "/share", label: t("nav.share"), icon: QrCode },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-surface-raised pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto flex max-w-lg overflow-x-auto">
        {tabs.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/"
              ? pathname === "/" ||
                pathname.startsWith("/upload") ||
                pathname.startsWith("/brief") ||
                pathname.startsWith("/vitals")
              : pathname.startsWith(href);
          const color = active ? "text-primary" : "text-[#A2A89F]";
          return (
            <Link
              key={href}
              href={href}
              className="flex min-h-[52px] min-w-[56px] flex-1 flex-col items-center justify-center gap-0.5 py-2"
            >
              <Icon className={cn("h-5 w-5", color)} strokeWidth={1.8} aria-hidden />
              <span className={cn("text-[10px] font-semibold leading-tight", color)}>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
