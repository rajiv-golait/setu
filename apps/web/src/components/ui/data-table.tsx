import { cn } from "@/lib/cn";

export function DataTable({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("divide-y divide-border rounded-card border border-border bg-surface-raised", className)}>
      {children}
    </div>
  );
}

export function DataRow({
  children,
  className,
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  const Tag = onClick ? "button" : "div";
  return (
    <Tag
      type={onClick ? "button" : undefined}
      onClick={onClick}
      className={cn(
        "flex w-full items-start justify-between gap-3 px-4 py-3.5 text-left transition-colors",
        onClick && "hover:bg-[#F4F8F5] active:bg-[#EEF4F0]",
        className,
      )}
    >
      {children}
    </Tag>
  );
}

export function FlushList({ children, className }: { children: React.ReactNode; className?: string }) {
  return <ul className={cn("divide-y divide-border", className)}>{children}</ul>;
}

export function FlushListItem({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <li className={cn("py-3.5 first:pt-0", className)}>{children}</li>;
}
