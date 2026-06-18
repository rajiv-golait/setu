"use client";

import { useCallback } from "react";
import { usePatient } from "@/lib/hooks/use-patient";
import { localeFromPref, t as translate, type Locale } from "@/lib/i18n/messages";

export function useLocale(): { locale: Locale; t: (key: string) => string } {
  const { patient, ready } = usePatient();
  // Before patient record loads, keep neutral English chrome. Once loaded, follow saved pref.
  const locale = ready
    ? localeFromPref(patient?.langPref ?? "mr")
    : localeFromPref(patient?.langPref);
  const t = useCallback((key: string) => translate(locale, key), [locale]);
  return { locale, t };
}
