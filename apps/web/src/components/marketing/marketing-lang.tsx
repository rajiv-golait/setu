"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  MARKETING_LOCALES,
  marketingT,
  type MarketingLocale,
} from "@/lib/i18n/marketing";

const STORAGE_KEY = "setu-marketing-locale";

type Ctx = { locale: MarketingLocale; setLocale: (l: MarketingLocale) => void; t: (key: string) => string };

const MarketingLangContext = createContext<Ctx | null>(null);

export function MarketingLangProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<MarketingLocale>("en");

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as MarketingLocale | null;
    if (saved === "en" || saved === "mr" || saved === "hi") setLocaleState(saved);
  }, []);

  const setLocale = useCallback((l: MarketingLocale) => {
    setLocaleState(l);
    localStorage.setItem(STORAGE_KEY, l);
  }, []);

  const t = useCallback((key: string) => marketingT(locale, key), [locale]);

  return (
    <MarketingLangContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </MarketingLangContext.Provider>
  );
}

export function useMarketingLang() {
  const ctx = useContext(MarketingLangContext);
  if (!ctx) throw new Error("useMarketingLang requires MarketingLangProvider");
  return ctx;
}

export function MarketingLangToggle() {
  const { locale, setLocale } = useMarketingLang();
  return (
    <div
      className="flex rounded-full border border-border bg-surface-raised p-0.5 text-xs font-semibold"
      role="group"
      aria-label="Page language"
    >
      {MARKETING_LOCALES.map(({ id, label }) => (
        <button
          key={id}
          type="button"
          onClick={() => setLocale(id)}
          className={`min-w-[2rem] rounded-full px-2 py-1 transition-colors ${
            locale === id ? "bg-primary text-white" : "text-text-muted hover:text-primary"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
