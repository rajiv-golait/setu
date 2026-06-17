"use client";

import { useState } from "react";
import { Download, FileText } from "lucide-react";
import { SecondaryButton } from "@/components/ui/buttons";
import { API_BASE } from "@/lib/constants";
import {
  getBriefFhir,
  getEsanjeewaniExport,
  getPublicEsanjeewani,
  getPublicFhirBundle,
} from "@/lib/api";

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function BriefExportActions({
  patientId,
  briefId,
  shareToken,
}: {
  patientId?: string;
  briefId?: string;
  shareToken?: string;
}) {
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);

  const fhirFilename = `setu-${briefId ?? shareToken ?? "brief"}.fhir.json`;

  const onFhir = async () => {
    setBusy("fhir");
    try {
      const bundle = shareToken
        ? await getPublicFhirBundle(shareToken)
        : await getBriefFhir(patientId!);
      downloadBlob(JSON.stringify(bundle, null, 2), fhirFilename, "application/json");
    } finally {
      setBusy(null);
    }
  };

  const onEsanjeewani = async () => {
    setBusy("esanje");
    try {
      const text = shareToken
        ? await getPublicEsanjeewani(shareToken)
        : await getEsanjeewaniExport(patientId!);
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="mt-4 flex flex-col gap-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-text-faint">
        Export for health systems
      </p>
      <SecondaryButton onClick={onFhir} disabled={busy === "fhir"}>
        <Download className="h-4 w-4" aria-hidden />
        {busy === "fhir" ? "Preparing…" : "Download FHIR JSON"}
      </SecondaryButton>
      <SecondaryButton onClick={onEsanjeewani} disabled={busy === "esanje"}>
        <FileText className="h-4 w-4" aria-hidden />
        {copied ? "Copied!" : busy === "esanje" ? "Copying…" : "Copy for eSanjeevani referral"}
      </SecondaryButton>
      {shareToken && (
        <p className="text-[11px] text-text-faint">
          Public export: {API_BASE}/brief/{shareToken}/fhir
        </p>
      )}
    </div>
  );
}
