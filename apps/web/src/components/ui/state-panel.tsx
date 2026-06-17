/** Empty / error states — design ref: SetuState.dc.html */

import { AlertTriangle, CloudOff, FileText } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";

export function EmptyDocuments({ onUpload }: { onUpload?: () => void }) {
  return (
    <div className="rounded-card border border-border bg-surface-raised px-5 py-8 text-center">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[#EEF4F0]">
        <FileText className="h-6 w-6 text-primary-light" strokeWidth={1.7} aria-hidden />
      </div>
      <p className="mt-3 text-[15px] font-semibold">No documents yet</p>
      <p className="mt-1 text-sm text-text-muted">Upload your first prescription or lab report to get started.</p>
      {onUpload && (
        <PrimaryButton className="mt-4" onClick={onUpload}>
          Upload a document
        </PrimaryButton>
      )}
    </div>
  );
}

export function ErrorPanel({
  title,
  message,
  code,
  retryable,
  onRetry,
}: {
  title: string;
  message: string;
  code?: string;
  retryable?: boolean;
  onRetry?: () => void;
}) {
  const Icon = retryable ? CloudOff : AlertTriangle;
  return (
    <div
      className={`rounded-card border p-4 ${
        retryable
          ? "border-warning-border border-l-4 border-l-warning bg-warning-bg"
          : "border-danger-border border-l-4 border-l-danger bg-danger-bg"
      }`}
    >
      <div className="flex gap-3">
        <Icon
          className={`mt-0.5 h-5 w-5 shrink-0 ${retryable ? "text-warning" : "text-danger"}`}
          strokeWidth={1.8}
          aria-hidden
        />
        <div>
          <p className={`text-sm font-semibold ${retryable ? "text-[#7C3A06]" : "text-[#7A1818]"}`}>
            {title}
          </p>
          <p className={`mt-1 text-sm ${retryable ? "text-[#8A5A2B]" : "text-[#A35454]"}`}>{message}</p>
          {code && (
            <p className="mt-1 font-mono text-[11px] text-text-faint">{code}</p>
          )}
        </div>
      </div>
      {retryable && onRetry && (
        <PrimaryButton className="mt-4" onClick={onRetry}>
          Try again
        </PrimaryButton>
      )}
    </div>
  );
}
