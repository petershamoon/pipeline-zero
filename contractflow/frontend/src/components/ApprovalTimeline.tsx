import { Badge } from "@/components/ui/badge";
import type { ApprovalStep } from "@/types/api";
import { cn } from "@/lib/utils";

export function ApprovalTimeline({ steps }: { steps: ApprovalStep[] }) {
  return (
    <div className="space-y-4">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-start gap-4">
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-medium",
              step.decision === "approved" &&
                "border-green-500 bg-green-50 text-green-700",
              step.decision === "rejected" &&
                "border-red-500 bg-red-50 text-red-700",
              step.decision === "pending" &&
                "border-muted-foreground/30 bg-muted text-muted-foreground",
            )}
          >
            {index + 1}
          </div>
          <div className="flex-1 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">
                Step {step.step_order}
              </span>
              <Badge
                variant={
                  step.decision === "approved"
                    ? "default"
                    : step.decision === "rejected"
                      ? "destructive"
                      : "secondary"
                }
                className={cn(
                  step.decision === "approved" &&
                    "bg-green-100 text-green-800",
                )}
              >
                {step.decision}
              </Badge>
            </div>
            {step.comment && (
              <p className="text-sm text-muted-foreground">{step.comment}</p>
            )}
            {step.decided_at && (
              <p className="text-xs text-muted-foreground">
                {new Date(step.decided_at).toLocaleString()}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
