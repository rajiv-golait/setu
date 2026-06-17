"use client";

import { useEffect } from "react";
import { usePatient } from "@/lib/hooks/use-patient";
import { localeFromPref } from "@/lib/i18n/messages";

export function LocaleHtmlLang() {
  const { patient } = usePatient();

  useEffect(() => {
    const lang = localeFromPref(patient?.langPref);
    document.documentElement.lang = lang;
    document.documentElement.classList.toggle(
      "font-devanagari",
      lang === "mr" || lang === "hi",
    );
  }, [patient?.langPref]);

  return null;
}
