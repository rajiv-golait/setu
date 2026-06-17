"use client";

import { usePatient } from "@/lib/hooks/use-patient";
import { localeFromPref, t, type Locale } from "@/lib/i18n/messages";

export function useLocale(): { locale: Locale; t: (key: string) => string } {
  const { patient } = usePatient();
  const locale = localeFromPref(patient?.langPref);
  return {
    locale,
    t: (key: string) => t(locale, key),
  };
}
