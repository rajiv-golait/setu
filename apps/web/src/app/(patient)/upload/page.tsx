"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Check } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { uploadDocument } from "@/lib/api";
import { compressImage, wasCompressed } from "@/lib/image-compress";
import { enqueueUpload } from "@/lib/offline-queue";
import { usePatient } from "@/lib/hooks/use-patient";
import { formatFileSize, mimeLabel, saveUploadMeta } from "@/lib/upload-meta";

const DOC_TYPES = ["Lab report", "Prescription", "Discharge summary"] as const;

export default function UploadPage() {
  const router = useRouter();
  const { patient, ensurePatient } = usePatient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [docType, setDocType] = useState<(typeof DOC_TYPES)[number]>("Lab report");
  const [uploading, setUploading] = useState(false);
  const [compressed, setCompressed] = useState(false);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    if (file.type.startsWith("image/")) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    }
    setPreviewUrl(null);
  }, [file]);

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
      const prepared = await compressImage(file);
      setCompressed(wasCompressed(file, prepared));
      saveUploadMeta({
        fileName: prepared.name,
        size: prepared.size,
        mime: prepared.type || "application/octet-stream",
      });

      if (!navigator.onLine) {
        await enqueueUpload({
          id: crypto.randomUUID(),
          patientId: p.id,
          blob: prepared,
          docType,
          filename: prepared.name,
        });
        alert("Saved offline — will upload when you're back online.");
        router.push("/");
        return;
      }

      const { job_id } = await uploadDocument(p.id, prepared, docType);
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

      <div className="relative mt-5 flex aspect-[4/5] items-center justify-center overflow-hidden rounded-[14px] border border-[#D8E0DA] bg-[repeating-linear-gradient(45deg,#F4F8F5,#F4F8F5_8px,#EEF4F0_8px,#EEF4F0_16px)]">
        {previewUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={previewUrl} alt="Document preview" className="h-full w-full object-contain" />
        ) : file?.type === "application/pdf" ? (
          <span className="text-sm font-semibold text-primary">PDF ready to upload</span>
        ) : null}
        {file && (
          <span className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-2 rounded-full bg-success-bg px-3 py-1.5 text-sm font-semibold text-success shadow-card">
            <Check className="h-4 w-4" /> Looks clear
          </span>
        )}
        {!file && <span className="text-sm text-text-muted">No file selected</span>}
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
          {file.name} · {formatFileSize(file.size)} · {mimeLabel(file.type || "")} · within 15 MB limit
          {compressed && (
            <span className="ml-2 rounded-full bg-info-bg px-2 py-0.5 text-xs font-semibold text-info">
              Compressed for slow network
            </span>
          )}
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
