"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Camera, Check, FileText, ImagePlus, X } from "lucide-react";
import { PrimaryButton, SecondaryButton } from "@/components/ui/buttons";
import { BackLink } from "@/components/ui/back-link";
import { PageHeader } from "@/components/ui/page-header";
import { uploadDocument, uploadDocumentsBatch } from "@/lib/api";
import { cn } from "@/lib/cn";
import { compressImage, wasCompressed } from "@/lib/image-compress";
import { enqueueUpload } from "@/lib/offline-queue";
import { usePatient } from "@/lib/hooks/use-patient";
import { formatFileSize, mimeLabel, saveUploadMeta } from "@/lib/upload-meta";

const DOC_TYPES = ["Lab report", "Prescription", "Discharge summary"] as const;
const MAX_FILES = 20;
const MAX_BYTES = 15 * 1024 * 1024;

type SelectedFile = {
  file: File;
  previewUrl: string | null;
  compressed: boolean;
};

export default function UploadPage() {
  const router = useRouter();
  const { patient, ensurePatient } = usePatient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<SelectedFile[]>([]);
  const [docType, setDocType] = useState<(typeof DOC_TYPES)[number]>("Lab report");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    return () => {
      for (const entry of files) {
        if (entry.previewUrl) URL.revokeObjectURL(entry.previewUrl);
      }
    };
  }, [files]);

  const addFiles = (incoming: FileList | File[] | null) => {
    if (!incoming?.length) return;
    const list = Array.from(incoming);
    const valid: SelectedFile[] = [];
    for (const f of list) {
      if (f.size > MAX_BYTES) {
        alert(`${f.name} is over 15 MB and was skipped`);
        continue;
      }
      valid.push({
        file: f,
        previewUrl: f.type.startsWith("image/") ? URL.createObjectURL(f) : null,
        compressed: false,
      });
    }
    if (!valid.length) return;
    setFiles((prev) => {
      const merged = [...prev, ...valid];
      if (merged.length > MAX_FILES) {
        alert(`Maximum ${MAX_FILES} files per upload`);
        return merged.slice(0, MAX_FILES);
      }
      return merged;
    });
  };

  const removeFile = (index: number) => {
    setFiles((prev) => {
      const next = [...prev];
      const [removed] = next.splice(index, 1);
      if (removed?.previewUrl) URL.revokeObjectURL(removed.previewUrl);
      return next;
    });
  };

  const openPicker = (capture?: boolean) => {
    const input = fileRef.current;
    if (!input) return;
    if (capture) {
      input.setAttribute("capture", "environment");
    } else {
      input.removeAttribute("capture");
    }
    input.click();
  };

  const submit = async () => {
    if (!files.length) return;
    setUploading(true);
    try {
      const p = patient ?? (await ensurePatient());
      const preparedEntries = await Promise.all(
        files.map(async (entry) => {
          const prepared = await compressImage(entry.file);
          return {
            ...entry,
            file: prepared,
            compressed: wasCompressed(entry.file, prepared),
          };
        }),
      );
      setFiles(preparedEntries);

      const preparedFiles = preparedEntries.map((e) => e.file);
      const first = preparedFiles[0];
      saveUploadMeta({
        fileName:
          preparedFiles.length === 1
            ? first.name
            : `${preparedFiles.length} documents`,
        size: preparedFiles.reduce((sum, f) => sum + f.size, 0),
        mime: first.type || "application/octet-stream",
      });

      if (!navigator.onLine) {
        for (const f of preparedFiles) {
          await enqueueUpload({
            id: crypto.randomUUID(),
            patientId: p.id,
            blob: f,
            docType,
            filename: f.name,
          });
        }
        alert("Saved offline — will upload when you're back online.");
        router.push("/");
        return;
      }

      if (preparedFiles.length === 1) {
        const { job_id } = await uploadDocument(p.id, preparedFiles[0], docType);
        router.push(`/progress/${job_id}`);
        return;
      }

      const { items } = await uploadDocumentsBatch(p.id, preparedFiles, docType);
      const jobIds = items.map((item) => item.job_id).join(",");
      router.push(`/progress/batch?jobs=${encodeURIComponent(jobIds)}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Upload failed");
      setUploading(false);
    }
  };

  const hasFiles = files.length > 0;
  const singlePreview = files.length === 1 ? files[0] : null;

  return (
    <div className="animate-setu-fade flex min-h-0 flex-1 flex-col px-4 pb-5 pt-3">
      <BackLink className="mb-3" />
      <PageHeader
        title={hasFiles ? "Review documents" : "Add documents"}
        subtitle={
          hasFiles
            ? `${files.length} selected — check they are readable before processing.`
            : "Choose the type, then take photos or pick files (up to 20)."
        }
      />

      <div className="mt-4 flex flex-wrap gap-2">
        {DOC_TYPES.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setDocType(t)}
            className={cn(
              "rounded-full px-3 py-1.5 text-[13px] font-semibold transition-colors",
              docType === t
                ? "bg-primary text-white shadow-sm"
                : "border border-border bg-surface-raised text-text-muted",
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <input
        ref={fileRef}
        type="file"
        accept="image/*,application/pdf"
        multiple
        className="hidden"
        onChange={(e) => {
          addFiles(e.target.files);
          e.target.value = "";
        }}
      />

      {!hasFiles ? (
        <div className="mt-5 flex min-h-0 flex-1 flex-col">
          <button
            type="button"
            onClick={() => openPicker(true)}
            className="flex min-h-[220px] flex-1 flex-col items-center justify-center gap-3 rounded-hero border-2 border-dashed border-primary/35 bg-[#F4F8F5] px-6 py-8 text-center transition-colors hover:border-primary/55 hover:bg-[#EEF4F0]"
          >
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Camera className="h-7 w-7" strokeWidth={1.8} />
            </span>
            <span>
              <span className="block font-display text-[17px] font-semibold text-text">
                Take a photo
              </span>
              <span className="mt-1 block text-sm text-text-muted">
                Lay papers flat · good light · all corners visible
              </span>
            </span>
          </button>

          <div className="mt-4 grid grid-cols-2 gap-2.5">
            <SecondaryButton onClick={() => openPicker(true)} className="!py-3 text-sm">
              <Camera className="h-4 w-4" />
              Camera
            </SecondaryButton>
            <SecondaryButton onClick={() => openPicker(false)} className="!py-3 text-sm">
              <ImagePlus className="h-4 w-4" />
              Gallery / PDF
            </SecondaryButton>
          </div>

          <p className="mt-4 text-center text-xs text-text-faint">
            JPG, PNG, or PDF · up to 15 MB each · up to {MAX_FILES} files
          </p>
        </div>
      ) : (
        <div className="mt-5 flex min-h-0 flex-1 flex-col">
          {singlePreview && (
            <div className="relative mb-4 flex max-h-[min(40vh,320px)] min-h-[160px] items-center justify-center overflow-hidden rounded-hero border border-border bg-[#1a1a1a]/[0.03] shadow-card">
              {singlePreview.previewUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={singlePreview.previewUrl}
                  alt="Document preview"
                  className="max-h-full max-w-full object-contain"
                />
              ) : (
                <div className="flex flex-col items-center gap-2 px-6 text-center text-text-muted">
                  <FileText className="h-10 w-10 text-primary" strokeWidth={1.5} />
                  <span className="text-sm font-semibold text-text">PDF ready to upload</span>
                </div>
              )}
              <span className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-1.5 rounded-full border border-success-border bg-success-bg/95 px-3 py-1.5 text-xs font-semibold text-success shadow-sm backdrop-blur-sm">
                <Check className="h-3.5 w-3.5" /> Looks clear
              </span>
            </div>
          )}

          <ul className="max-h-[40vh] space-y-2 overflow-y-auto">
            {files.map((entry, index) => (
              <li
                key={`${entry.file.name}-${index}`}
                className="flex items-center gap-3 rounded-card border border-border bg-surface-raised px-3 py-2.5"
              >
                <FileText className="h-5 w-5 shrink-0 text-primary" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">{entry.file.name}</p>
                  <p className="text-xs text-text-muted">
                    {formatFileSize(entry.file.size)} · {mimeLabel(entry.file.type || "")}
                    {entry.compressed && (
                      <span className="ml-2 rounded-full bg-info-bg px-1.5 py-0.5 text-[10px] font-semibold text-info">
                        Compressed
                      </span>
                    )}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => removeFile(index)}
                  className="rounded-full p-1 text-text-muted hover:bg-border"
                  aria-label={`Remove ${entry.file.name}`}
                >
                  <X className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>

          <div className="mt-auto space-y-2.5 pt-5">
            <PrimaryButton disabled={uploading} onClick={submit}>
              {uploading
                ? "Uploading…"
                : files.length === 1
                  ? "Upload & process"
                  : `Upload & process ${files.length} documents`}
            </PrimaryButton>
            <SecondaryButton
              onClick={() => openPicker(false)}
              disabled={uploading}
              aria-label="Add more files"
            >
              Add more files
            </SecondaryButton>
          </div>
        </div>
      )}
    </div>
  );
}
