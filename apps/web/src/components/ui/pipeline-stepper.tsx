import { Check } from "lucide-react";
import { cn } from "@/lib/cn";

const STAGES = ["extraction", "validation", "memory", "explanation", "brief", "share"] as const;

const LABELS: Record<(typeof STAGES)[number], string> = {
  extraction: "Reading your document",
  validation: "Checking details",
  memory: "Updating your health memory",
  explanation: "Writing plain-language summary",
  brief: "Preparing doctor brief",
  share: "Ready to share",
};

export function PipelineStepper({
  completedStages,
  currentStage,
  failedAt,
}: {
  completedStages: string[];
  currentStage?: string | null;
  failedAt?: string | null;
}) {
  return (
    <ol className="relative space-y-0">
      {STAGES.map((stage, i) => {
        const done = completedStages.includes(stage);
        const active = currentStage === stage && !failedAt;
        const failed = failedAt === stage;
        const pending = !done && !active && !failed;

        return (
          <li key={stage} className="flex gap-3 pb-6 last:pb-0">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold",
                  done && "border-success bg-success text-white",
                  active && "border-primary bg-primary text-white",
                  failed && "border-danger bg-danger-bg text-danger",
                  pending && "border-border bg-surface-raised text-text-faint",
                )}
              >
                {done ? <Check className="h-4 w-4" strokeWidth={2.5} /> : i + 1}
              </div>
              {i < STAGES.length - 1 && (
                <div
                  className={cn("mt-1 w-0.5 flex-1 min-h-[24px]", done ? "bg-success/40" : "bg-border")}
                />
              )}
            </div>
            <div className="min-w-0 pt-1">
              <p
                className={cn(
                  "text-sm font-semibold",
                  done && "text-text",
                  active && "text-primary",
                  failed && "text-danger",
                  pending && "text-text-faint",
                )}
              >
                {LABELS[stage]}
              </p>
              {active && <p className="mt-0.5 text-xs text-text-muted">In progress…</p>}
              {failed && <p className="mt-0.5 text-xs text-danger">Could not complete this step</p>}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
