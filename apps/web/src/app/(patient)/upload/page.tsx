"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { uploadDocument } from "@/lib/api";
import { usePatient } from "@/lib/hooks/use-patient";

const DOC_TYPES = ["Lab report", "Prescription", "Discharge summary"] as const;

export default function UploadPage() {
  const router = useRouter();
  const { patient, ensurePatient } = usePatient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<(typeof DOC_TYPES)[number]>("Lab report");
  const [uploading, setUploading] = useState(false);

  const onFile = (f: File | null) => {
    if (!f) return;
    if (f.size > 15 * 1024 * 1024) {
      alert("File must be under 15 MB");
      return;
    }
    setFile(f);
  };

  const submit = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const p = patient ?? (await ensurePatient());
      const { job_id } = await uploadDocument(p.id, file);
      router.push(`/progress/${job_id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Upload failed");
      setUploading(false);
    }
  };

  return (
    <div className="animate-setu-fade px-5 pb-8 pt-4">
      <button
        type="button"
        onClick={() => router.back()}
        className="mb-4 flex items-center gap-2 text-sm font-semibold text-primary"
      >
        <ArrowLeft className="h-4 w-4" /> Back
      </button>

      <h1 className="text-[23px] font-semibold">Review photo</h1>
      <p className="text-sm text-text-muted">Is it clear and readable?</p>

      <div className="mt-5 flex aspect-[4/5] items-center justify-center rounded-[14px] border border-[#D8E0DA] bg-[repeating-linear-gradient(45deg,#F4F8F5,#F4F8F5_8px,#EEF4F0_8px,#EEF4F0_16px)]">
        {file ? (
          <span className="flex items-center gap-2 rounded-full bg-success-bg px-3 py-1.5 text-sm font-semibold text-success">
            <Check className="h-4 w-4" /> Looks clear
          </span>
        ) : (
          <span className="text-sm text-text-muted">No file selected</span>
        )}
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*,application/pdf"
        className="hidden"
        onChange={(e) => onFile(e.target.files?.[0] ?? null)}
      />

      {file && (
        <p className="mt-3 text-sm text-text-muted">
          {file.name} · {(file.size / 1024 / 1024).toFixed(1)} MB · within 15 MB limit
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {DOC_TYPES.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setDocType(t)}
            className={`rounded-full px-3 py-1.5 text-[13px] font-semibold ${
              docType === t
                ? "bg-primary text-white"
                : "border border-border bg-surface-raised text-text-muted"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <p className="mt-3 text-xs text-text-faint">Tip: avoid shadows and keep all corners visible.</p>

      <PrimaryButton className="mt-5" disabled={!file || uploading} onClick={submit}>
        {uploading ? "Uploading…" : "Upload & process"}
      </PrimaryButton>
      <SecondaryButton
        className="mt-2.5"
        onClick={() => fileRef.current?.click()}
        aria-label="Choose or retake photo"
      >
        {file ? "Retake photo" : "Choose file"}
      </SecondaryButton>
    </div>
  );
}
