import { WarmCard } from "@/components/ui/warm-card";
import { cn } from "@/lib/cn";

export function StatCard({
  label,
  value,
  className,
}: {
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <WarmCard className={cn("text-center sm:text-left", className)}>
      <p className="font-display text-2xl font-bold tabular-nums text-primary">{value}</p>
      <p className="mt-1 text-sm text-text-muted">{label}</p>
    </WarmCard>
  );
}
