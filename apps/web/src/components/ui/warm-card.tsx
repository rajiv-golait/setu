import { cn } from "@/lib/cn";

const variants = {
  raised: "rounded-card border border-border bg-surface-raised p-4 shadow-card",
  flat: "rounded-card border border-border/60 bg-surface-raised/80 p-3.5",
  inset: "rounded-card border border-border bg-[#F4F0E8] p-4",
  hero: "rounded-hero border border-border bg-surface-raised p-4 shadow-raised border-t-[3px] border-t-primary",
} as const;

export function WarmCard({
  children,
  variant = "raised",
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement> & { variant?: keyof typeof variants }) {
  return (
    <div className={cn(variants[variant], className)} {...props}>
      {children}
    </div>
  );
}
