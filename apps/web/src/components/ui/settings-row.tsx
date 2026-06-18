import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/cn";

export function SettingsGroup({
  title,
  children,
  className,
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      {title && <p className="mb-2 px-1 text-label text-text-muted">{title}</p>}
      <div className="overflow-hidden rounded-card border border-border bg-surface-raised divide-y divide-border">
        {children}
      </div>
    </div>
  );
}

export function SettingsRow({
  label,
  description,
  href,
  onClick,
  trailing,
  children,
}: {
  label: string;
  description?: string;
  href?: string;
  onClick?: () => void;
  trailing?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const inner = (
    <>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-text">{label}</p>
        {description && <p className="mt-0.5 text-xs text-text-muted">{description}</p>}
        {children}
      </div>
      {trailing ?? (href && <ChevronRight className="h-4 w-4 shrink-0 text-text-faint" aria-hidden />)}
    </>
  );

  const className =
    "flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-[#F4F8F5]";

  if (href) {
    return (
      <Link href={href} className={className}>
        {inner}
      </Link>
    );
  }

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={className}>
        {inner}
      </button>
    );
  }

  return <div className={cn(className, "cursor-default")}>{inner}</div>;
}
