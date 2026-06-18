"use client";

import { Download, Share, Smartphone, X } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { useLocale } from "@/lib/hooks/use-locale";
import { usePwaInstall } from "@/lib/hooks/use-pwa-install";

const HIDE_PREFIXES = [
  "/login",
  "/onboarding",
  "/admin/login",
  "/doctor/login",
  "/share/",
  "/brief/",
];

export function InstallAppPrompt({ pathname }: { pathname: string }) {
  const { t } = useLocale();
  const { canShow, isIos, hasNativePrompt, dismiss, promptInstall } = usePwaInstall();

  if (HIDE_PREFIXES.some((p) => pathname.startsWith(p))) return null;
  if (!canShow) return null;

  return (
    <div
      className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-lg px-4 pb-[max(1rem,env(safe-area-inset-bottom))]"
      role="dialog"
      aria-labelledby="pwa-install-title"
    >
      <div className="rounded-hero border border-border bg-surface-raised p-4 shadow-[0_-8px_32px_rgba(0,0,0,0.12)]">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Smartphone className="h-5 w-5" strokeWidth={1.8} />
          </span>
          <div className="min-w-0 flex-1">
            <p id="pwa-install-title" className="font-display text-[17px] font-semibold text-text">
              {t("pwa.install.title")}
            </p>
            <p className="mt-1 text-sm text-text-muted">{t("pwa.install.subtitle")}</p>
          </div>
          <button
            type="button"
            onClick={dismiss}
            className="rounded-full p-1 text-text-muted hover:bg-border"
            aria-label={t("pwa.install.dismiss")}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {isIos && !hasNativePrompt ? (
          <ol className="mt-4 space-y-2.5 text-sm text-text">
            <li className="flex items-center gap-2.5 rounded-card bg-surface px-3 py-2">
              <Share className="h-4 w-4 shrink-0 text-primary" />
              <span>{t("pwa.install.ios.step1")}</span>
            </li>
            <li className="flex items-center gap-2.5 rounded-card bg-surface px-3 py-2">
              <span className="flex h-4 w-4 shrink-0 items-center justify-center text-xs font-bold text-primary">
                +
              </span>
              <span>{t("pwa.install.ios.step2")}</span>
            </li>
          </ol>
        ) : (
          <div className="mt-4">
            <PrimaryButton onClick={() => void promptInstall()}>
              <Download className="h-4 w-4" />
              {t("pwa.install.android")}
            </PrimaryButton>
          </div>
        )}

        <SecondaryButton className="mt-2" onClick={dismiss}>
          {t("pwa.install.later")}
        </SecondaryButton>
      </div>
    </div>
  );
}

/** Compact row for Settings — always available when installable. */
export function InstallAppSettingsRow() {
  const { t } = useLocale();
  const { installed, installable, isIos, hasNativePrompt, openPrompt, promptInstall } = usePwaInstall();

  if (installed) {
    return (
      <p className="text-sm text-success">{t("pwa.install.installed")}</p>
    );
  }

  if (!installable) {
    return (
      <p className="text-sm text-text-muted">{t("pwa.install.unavailable")}</p>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-sm text-text-muted">{t("pwa.install.settingsHint")}</p>
      {isIos && !hasNativePrompt ? (
        <SecondaryButton onClick={openPrompt}>{t("pwa.install.showSteps")}</SecondaryButton>
      ) : (
        <PrimaryButton onClick={() => void promptInstall()}>
          <Download className="h-4 w-4" />
          {t("pwa.install.android")}
        </PrimaryButton>
      )}
    </div>
  );
}
