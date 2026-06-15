"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Camera, LayoutList, QrCode } from "lucide-react";
import { cn } from "@/lib/cn";

const tabs = [
  { href: "/", label: "Home", icon: Camera },
  { href: "/memory", label: "Memory", icon: LayoutList },
  { href: "/share", label: "Share", icon: QrCode },
];

export function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-surface-raised pb-[env(safe-area-inset-bottom)]">
      <div className="mx-auto flex max-w-lg">
        {tabs.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/"
              ? pathname === "/" || pathname.startsWith("/upload") || pathname.startsWith("/brief")
              : pathname.startsWith(href);
          const color = active ? "text-primary" : "text-[#A2A89F]";
          return (
            <Link
              key={href}
              href={href}
              className="flex min-h-[52px] flex-1 flex-col items-center justify-center gap-1 py-2"
            >
              <Icon className={cn("h-[22px] w-[22px]", color)} strokeWidth={1.8} aria-hidden />
              <span className={cn("text-[11px] font-semibold", color)}>{label}</span>
              <span
                className={cn(
                  "h-[2.5px] w-5 rounded-full",
                  active ? "bg-primary" : "bg-transparent",
                )}
              />
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
