"use client";

import { useCallback, useEffect, useState } from "react";

const DISMISS_KEY = "setu-pwa-install-dismissed";
const DISMISS_DAYS = 14;

type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

function isIosDevice(): boolean {
  if (typeof navigator === "undefined") return false;
  return (
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1)
  );
}

function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(display-mode: standalone)").matches ||
    (navigator as Navigator & { standalone?: boolean }).standalone === true
  );
}

function wasDismissedRecently(): boolean {
  try {
    const raw = localStorage.getItem(DISMISS_KEY);
    if (!raw) return false;
    const ts = Number(raw);
    if (!Number.isFinite(ts)) return false;
    return Date.now() - ts < DISMISS_DAYS * 24 * 60 * 60 * 1000;
  } catch {
    return false;
  }
}

export function usePwaInstall() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [isIos, setIsIos] = useState(false);
  const [installed, setInstalled] = useState(false);
  const [canShow, setCanShow] = useState(false);

  useEffect(() => {
    setIsIos(isIosDevice());
    setInstalled(isStandalone());

    const onInstallable = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      if (!wasDismissedRecently() && !isStandalone()) {
        setCanShow(true);
      }
    };

    const onInstalled = () => {
      setInstalled(true);
      setCanShow(false);
      setDeferredPrompt(null);
    };

    window.addEventListener("beforeinstallprompt", onInstallable);
    window.addEventListener("appinstalled", onInstalled);

    if (isIosDevice() && !isStandalone() && !wasDismissedRecently()) {
      const t = window.setTimeout(() => setCanShow(true), 2500);
      return () => {
        clearTimeout(t);
        window.removeEventListener("beforeinstallprompt", onInstallable);
        window.removeEventListener("appinstalled", onInstalled);
      };
    }

    return () => {
      window.removeEventListener("beforeinstallprompt", onInstallable);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  const dismiss = useCallback(() => {
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch {
      /* ignore */
    }
    setCanShow(false);
  }, []);

  const promptInstall = useCallback(async () => {
    if (!deferredPrompt) return false;
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    setDeferredPrompt(null);
    if (outcome === "accepted") {
      setInstalled(true);
      setCanShow(false);
      return true;
    }
    return false;
  }, [deferredPrompt]);

  const openPrompt = useCallback(() => {
    if (installed) return;
    setCanShow(true);
  }, [installed]);

  const installable = Boolean(deferredPrompt) || (isIos && !installed);

  return {
    canShow: canShow && !installed && installable,
    isIos,
    installed,
    installable,
    hasNativePrompt: Boolean(deferredPrompt),
    dismiss,
    promptInstall,
    openPrompt,
  };
}
