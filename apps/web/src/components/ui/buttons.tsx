import { cn } from "@/lib/cn";

export function PrimaryButton({
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "flex min-h-[44px] w-full items-center justify-center gap-2 rounded-[13px] bg-primary px-4 py-[15px] text-base font-semibold text-white transition-colors hover:bg-primary-pressed",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function SecondaryButton({
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type="button"
      className={cn(
        "flex min-h-[44px] w-full items-center justify-center gap-2 rounded-[13px] border border-[#D8E0DA] bg-surface-raised px-4 py-[13px] text-[15px] font-semibold text-primary transition-colors hover:bg-[#F4F8F5]",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function SectionHeader({
  title,
  badge,
}: {
  title: string;
  badge?: string;
}) {
  return (
    <div className="mb-3 mt-6 flex items-center gap-2 px-0.5">
      <h2 className="text-[13px] font-semibold uppercase tracking-[0.06em] text-[#3D4A42]">
        {title}
      </h2>
      <div className="h-px flex-1 bg-border" />
      {badge && (
        <span className="rounded-full border border-border bg-surface-raised px-2 py-0.5 text-[11px] text-text-muted">
          {badge}
        </span>
      )}
    </div>
  );
}
