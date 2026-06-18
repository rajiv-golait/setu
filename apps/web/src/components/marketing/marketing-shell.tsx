"use client";

import Link from "next/link";
import { MarketingLangProvider, MarketingLangToggle, useMarketingLang } from "./marketing-lang";

function ShellInner({
  children,
  variant = "patient",
}: {
  children: React.ReactNode;
  variant?: "patient" | "doctor";
}) {
  const { t } = useMarketingLang();

  return (
    <div className="min-h-screen bg-surface text-text">
      <header className="sticky top-0 z-40 border-b border-border bg-surface-raised/95 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-3 px-4 py-3">
          <Link
            href={variant === "doctor" ? "/for-doctors" : "/welcome"}
            className="flex items-center gap-2"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/setu-logo.webp"
              alt="Setu"
              width={32}
              height={32}
              className="h-9 w-9 rounded-lg object-contain"
            />
            <span className="font-display text-lg font-semibold">
              Setu{variant === "doctor" ? " · Doctor" : ""}
            </span>
          </Link>
          <nav className="flex items-center gap-2 sm:gap-3 text-sm font-semibold">
            <MarketingLangToggle />
            {variant === "patient" ? (
              <>
                <Link
                  href="/for-doctors"
                  className="hidden text-text-muted hover:text-primary sm:inline"
                >
                  {t("nav.forDoctors")}
                </Link>
                <Link
                  href="/login"
                  className="rounded-full bg-primary px-3 py-2 text-white hover:bg-primary-pressed sm:px-4"
                >
                  {t("nav.getStarted")}
                </Link>
              </>
            ) : (
              <>
                <Link href="/welcome" className="hidden text-text-muted hover:text-primary sm:inline">
                  {t("nav.forFamilies")}
                </Link>
                <Link
                  href="/doctor/login"
                  className="rounded-full bg-primary px-3 py-2 text-white hover:bg-primary-pressed sm:px-4"
                >
                  {t("nav.doctorSignIn")}
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}

export function MarketingShell({
  children,
  variant = "patient",
}: {
  children: React.ReactNode;
  variant?: "patient" | "doctor";
}) {
  return (
    <MarketingLangProvider>
      <ShellInner variant={variant}>{children}</ShellInner>
    </MarketingLangProvider>
  );
}
