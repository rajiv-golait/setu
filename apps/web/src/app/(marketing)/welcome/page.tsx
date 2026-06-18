"use client";

import Link from "next/link";
import { Check } from "lucide-react";
import { MarketingShell } from "@/components/marketing/marketing-shell";
import { useMarketingLang } from "@/components/marketing/marketing-lang";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";

function WelcomeContent() {
  const { t } = useMarketingLang();

  const steps = [
    { title: t("welcome.step1.title"), body: t("welcome.step1.body") },
    { title: t("welcome.step2.title"), body: t("welcome.step2.body") },
    { title: t("welcome.step3.title"), body: t("welcome.step3.body") },
  ];

  const faq = [
    { q: t("welcome.faq1.q"), a: t("welcome.faq1.a") },
    { q: t("welcome.faq2.q"), a: t("welcome.faq2.a") },
    { q: t("welcome.faq3.q"), a: t("welcome.faq3.a") },
  ];

  const privacyPoints = [t("welcome.privacy.p1"), t("welcome.privacy.p2"), t("welcome.privacy.p3")];

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute inset-0 -z-10 opacity-70"
          style={{
            background:
              "radial-gradient(60rem 30rem at 85% -10%, rgba(20,184,166,0.10), transparent 60%)",
          }}
          aria-hidden
        />
        <div className="mx-auto max-w-6xl px-4 pb-16 pt-12 sm:pt-16">
          <div className="grid items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
            <div>
              <p className="text-label text-primary">{t("welcome.eyebrow")}</p>
              <h1 className="mt-3 font-display text-[2.6rem] font-bold leading-[1.05] tracking-tight text-text sm:text-[3.4rem]">
                {t("welcome.title")}
              </h1>
              <p className="mt-5 max-w-xl text-body-lg text-text-muted">{t("welcome.subtitle")}</p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/login" className="inline-block min-w-[170px]">
                  <PrimaryButton>{t("welcome.cta.primary")}</PrimaryButton>
                </Link>
                <Link href="/upload" className="inline-block min-w-[170px]">
                  <SecondaryButton>{t("welcome.cta.secondary")}</SecondaryButton>
                </Link>
              </div>
              <p className="mt-5 flex items-center gap-2 text-sm text-text-muted">
                <Check className="h-4 w-4 shrink-0 text-success" strokeWidth={2.4} />
                {t("welcome.trust")}
              </p>
            </div>

            <PhonePreview t={t} />
          </div>
        </div>
      </section>

      {/* How it works — 3-up */}
      <section className="border-y border-border bg-surface-raised px-4 py-16">
        <div className="mx-auto max-w-6xl">
          <h2 className="font-display text-3xl font-semibold tracking-tight">{t("welcome.how")}</h2>
          <p className="mt-2 max-w-xl text-text-muted">{t("welcome.how.sub")}</p>
          <ol className="mt-10 grid gap-x-8 gap-y-10 md:grid-cols-3">
            {steps.map(({ title, body }, i) => (
              <li key={title} className="relative">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary font-display text-base font-bold text-white">
                  {i + 1}
                </span>
                <h3 className="mt-4 font-display text-lg font-semibold">{title}</h3>
                <p className="mt-1.5 text-[15px] leading-relaxed text-text-muted">{body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Privacy — Setu's differentiator */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <p className="text-label text-primary">{t("welcome.privacy.eyebrow")}</p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-tight">
              {t("welcome.privacy.title")}
            </h2>
            <p className="mt-4 max-w-lg text-body-lg text-text-muted">{t("welcome.privacy.body")}</p>
          </div>
          <ul className="space-y-3">
            {privacyPoints.map((p) => (
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

      {/* FAQ */}
      <section className="border-t border-border bg-surface-raised px-4 py-16">
        <div className="mx-auto max-w-3xl">
          <h2 className="font-display text-3xl font-semibold tracking-tight">{t("welcome.faq.title")}</h2>
          <dl className="mt-8 divide-y divide-border">
            {faq.map(({ q, a }) => (
              <div key={q} className="py-5">
                <dt className="font-display text-lg font-semibold text-text">{q}</dt>
                <dd className="mt-2 leading-relaxed text-text-muted">{a}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="bg-primary px-4 py-16 text-center text-white">
        <h2 className="font-display text-3xl font-semibold tracking-tight">{t("welcome.closing.title")}</h2>
        <p className="mx-auto mt-3 max-w-md text-white/85">{t("welcome.closing.body")}</p>
        <Link href="/login" className="mx-auto mt-7 block max-w-xs">
          <button
            type="button"
            className="min-h-[44px] w-full rounded-[13px] bg-white px-4 py-3 font-semibold text-primary transition-colors hover:bg-surface"
          >
            {t("welcome.cta.primary")}
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
              <span className="font-display text-lg font-semibold">Setu</span>
            </div>
            <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm font-semibold text-text-muted">
              <Link href="/for-doctors" className="hover:text-primary">
                {t("nav.forDoctors")}
              </Link>
              <Link href="/login" className="hover:text-primary">
                {t("welcome.cta.primary")}
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

function PhonePreview({ t }: { t: (key: string) => string }) {
  return (
    <div className="relative mx-auto w-full max-w-sm">
      <div className="rounded-[30px] border border-border bg-surface-raised p-3 shadow-phone">
        <div className="overflow-hidden rounded-[22px] border border-border/60 bg-surface">
          <div className="border-b border-border/60 bg-surface-raised/80 px-5 py-3">
            <p className="text-label text-primary">{t("welcome.preview.today")}</p>
            <p className="mt-1 font-display text-2xl font-semibold tracking-tight">
              {t("welcome.preview.greeting")}
            </p>
          </div>
          <div className="space-y-2.5 p-5">
            <PreviewMed name="Metformin — after breakfast" badge="new" t={t} />
            <PreviewMed name="Amlodipine — evening" badge="taken" t={t} />
            <p className="pt-1 text-xs text-text-faint">
              Saathi keeps your medicines, labs, and trends in one place.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function PreviewMed({
  name,
  badge,
  t,
}: {
  name: string;
  badge: "new" | "taken";
  t: (key: string) => string;
}) {
  const isNew = badge === "new";
  return (
    <div
      className={`flex items-center justify-between rounded-card border px-4 py-3 ${
        isNew ? "border-marigold-border bg-marigold-bg" : "border-border bg-surface-raised"
      }`}
    >
      <span className="text-sm font-semibold text-text">{name}</span>
      {isNew ? (
        <span className="rounded-full bg-marigold px-2 py-0.5 text-xs font-semibold text-white">
          {t("welcome.preview.new")}
        </span>
      ) : (
        <span className="rounded-full bg-success-bg px-2 py-0.5 text-xs font-semibold text-success">
          Taken
        </span>
      )}
    </div>
  );
}

export default function WelcomePage() {
  return (
    <MarketingShell variant="patient">
      <WelcomeContent />
    </MarketingShell>
  );
}
