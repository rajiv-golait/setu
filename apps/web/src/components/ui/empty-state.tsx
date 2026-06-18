import { SetuAvatar } from "@/components/characters/setu-avatar";
import { PrimaryButton } from "@/components/ui/buttons";
import { cn } from "@/lib/cn";

export function EmptyState({
  title,
  message,
  actionLabel,
  onAction,
  variant = "default",
  className,
}: {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  variant?: "default" | "withSaathi" | "inline";
  className?: string;
}) {
  if (variant === "inline") {
    return (
      <div className={cn("rounded-card border border-dashed border-border bg-surface-raised/50 px-4 py-6 text-center", className)}>
        <p className="text-sm font-semibold text-text">{title}</p>
        <p className="mt-1 text-sm text-text-muted">{message}</p>
        {actionLabel && onAction && (
          <button type="button" onClick={onAction} className="mt-3 text-sm font-semibold text-primary">
            {actionLabel}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col items-center px-6 py-12 text-center", className)}>
      {variant === "withSaathi" && <SetuAvatar size={64} label="" />}
      <h2 className={cn("font-display text-lg font-semibold text-text", variant === "withSaathi" && "mt-4")}>
        {title}
      </h2>
      <p className="mt-2 max-w-xs text-sm text-text-muted">{message}</p>
      {actionLabel && onAction && (
        <div className="mt-6 w-full max-w-xs">
          <PrimaryButton onClick={onAction}>{actionLabel}</PrimaryButton>
        </div>
      )}
    </div>
  );
}
