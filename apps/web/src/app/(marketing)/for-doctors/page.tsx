"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { MarketingShell } from "@/components/marketing/marketing-shell";
import { useMarketingLang } from "@/components/marketing/marketing-lang";
import { PrimaryButton } from "@/components/ui/buttons";

function ForDoctorsContent() {
  const { t } = useMarketingLang();

  const features = [
    { title: t("doctors.f1.title"), body: t("doctors.f1.body") },
    { title: t("doctors.f2.title"), body: t("doctors.f2.body") },
    { title: t("doctors.f3.title"), body: t("doctors.f3.body") },
  ];

  const bandPoints = [t("doctors.band.p1"), t("doctors.band.p2"), t("doctors.band.p3")];

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10 opacity-70"
          style={{
            background:
              "radial-gradient(60rem 30rem at 85% -10%, rgba(15,118,110,0.10), transparent 60%)",
          }}
          aria-hidden
        />
        <div className="mx-auto max-w-6xl px-4 pb-16 pt-12 sm:pt-16">
          <div className="grid items-center gap-12 lg:grid-cols-[0.95fr_1.05fr]">
            <div>
              <p className="text-label text-primary">{t("doctors.eyebrow")}</p>
              <h1 className="mt-3 font-display text-[2.4rem] font-bold leading-[1.08] tracking-tight text-text sm:text-[3rem]">
                {t("doctors.title")}
              </h1>
              <p className="mt-5 max-w-lg text-body-lg text-text-muted">{t("doctors.subtitle")}</p>
              <Link href="/doctor/login" className="mt-8 inline-block min-w-[200px]">
                <PrimaryButton>{t("doctors.cta")}</PrimaryButton>
              </Link>
              <p className="mt-5 flex items-center gap-2 text-sm text-text-muted">
                <Check className="h-4 w-4 shrink-0 text-success" strokeWidth={2.4} />
                {t("doctors.trust")}
              </p>
            </div>

            <DashboardPreview t={t} />
          </div>
        </div>
      </section>

      {/* Benefits — 3-up */}
      <section className="border-y border-border bg-surface-raised px-4 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-display text-3xl font-semibold tracking-tight">
            {t("doctors.benefits.title")}
          </h2>
          <p className="mt-2 max-w-xl text-text-muted">{t("doctors.benefits.sub")}</p>
          <div className="mt-10 grid gap-x-8 gap-y-10 md:grid-cols-3">
            {features.map(({ title, body }, i) => (
              <div key={title}>
                <span className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-primary font-display text-base font-bold text-primary">
                  {i + 1}
                </span>
                <h3 className="mt-4 font-display text-lg font-semibold">{title}</h3>
                <p className="mt-1.5 text-[15px] leading-relaxed text-text-muted">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Trust band — non-diagnostic stance */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <p className="text-label text-primary">{t("doctors.band.eyebrow")}</p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight">
              {t("doctors.band.title")}
            </h2>
            <p className="mt-4 max-w-lg text-body-lg text-text-muted">{t("doctors.band.body")}</p>
          </div>
          <ul className="space-y-3">
            {bandPoints.map((p) => (
              <li
                key={p}
                className="flex items-center gap-3 rounded-card border border-border bg-surface-raised px-4 py-3.5"
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-success-bg">
                  <Check className="h-4 w-4 text-success" strokeWidth={2.4} />
                </span>
                <span className="font-medium text-text">{p}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="bg-primary px-4 py-16 text-center text-white">
        <h2 className="mx-auto max-w-2xl font-display text-3xl font-semibold tracking-tight">
          {t("doctors.closing.title")}
        </h2>
        <p className="mx-auto mt-3 max-w-md text-white/85">{t("doctors.closing.body")}</p>
        <Link href="/doctor/login" className="mx-auto mt-7 block max-w-xs">
          <button
            type="button"
            className="min-h-[44px] w-full rounded-[13px] bg-white px-4 py-3 font-semibold text-primary transition-colors hover:bg-surface"
          >
            {t("doctors.cta")}
          </button>
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-surface-raised">
        <div className="mx-auto max-w-6xl px-4 py-10">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/setu-logo.webp" alt="Setu" width={32} height={32} className="h-9 w-9 rounded-lg object-contain" />
              <span className="font-display text-lg font-semibold">Setu · Doctor</span>
            </div>
            <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm font-semibold text-text-muted">
              <Link href="/welcome" className="hover:text-primary">
                {t("nav.forFamilies")}
              </Link>
              <Link href="/doctor/login" className="hover:text-primary">
                {t("doctors.cta")}
              </Link>
            </nav>
          </div>
          <p className="mt-6 text-xs text-text-faint">
            {t("footer.tagline")} {t("footer.rights")}
          </p>
        </div>
      </footer>
    </>
  );
}

function DashboardPreview({ t }: { t: (key: string) => string }) {
  const stats = [
    { n: "3", l: "Pending" },
    { n: "5", l: "Today" },
    { n: "2", l: "Follow-ups" },
  ];
  return (
    <div className="rounded-[18px] border border-border bg-surface-raised p-2.5 shadow-phone">
      {/* browser chrome */}
      <div className="flex items-center gap-1.5 px-2 py-2">
        <span className="h-2.5 w-2.5 rounded-full bg-danger/40" />
        <span className="h-2.5 w-2.5 rounded-full bg-marigold/50" />
        <span className="h-2.5 w-2.5 rounded-full bg-success/40" />
        <span className="ml-3 text-xs text-text-faint">{t("doctors.preview")}</span>
      </div>
      <div className="overflow-hidden rounded-[12px] border border-border/60 bg-surface p-5">
        <div className="grid grid-cols-3 gap-2.5">
          {stats.map(({ n, l }) => (
            <div key={l} className="rounded-card border border-border bg-surface-raised px-3 py-4 text-center">
              <p className="font-display text-2xl font-bold tabular-nums text-primary">{n}</p>
              <p className="mt-0.5 text-xs text-text-muted">{l}</p>
            </div>
          ))}
        </div>
        <div className="mt-4 rounded-card border border-border bg-surface-raised px-4 py-3.5">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold">Priya S. · 54</p>
            <span className="rounded-full bg-marigold-bg px-2 py-0.5 text-[11px] font-semibold text-marigold">
              New request
            </span>
          </div>
          <p className="mt-0.5 text-xs text-text-muted">Diabetes follow-up · brief attached</p>
          <div className="mt-3 flex gap-2">
            <span className="rounded-full bg-success px-3 py-1 text-xs font-semibold text-white">Accept</span>
            <span className="rounded-full border border-border px-3 py-1 text-xs font-semibold text-text-muted">
              Decline
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ForDoctorsPage() {
  return (
    <MarketingShell variant="doctor">
      <ForDoctorsContent />
    </MarketingShell>
  );
}
