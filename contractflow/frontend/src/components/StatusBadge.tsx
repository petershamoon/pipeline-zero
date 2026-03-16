import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const statusConfig: Record<
  string,
  {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
  }
> = {
  draft: { label: "Draft", variant: "outline" },
  pending_approval: { label: "Pending Approval", variant: "default" },
  active: { label: "Active", variant: "default" },
  expired: { label: "Expired", variant: "destructive" },
  terminated: { label: "Terminated", variant: "secondary" },
  archived: { label: "Archived", variant: "secondary" },
};

export function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] ?? {
    label: status,
    variant: "outline" as const,
  };
  return (
    <Badge
      variant={config.variant}
      className={cn(
        status === "active" &&
          "bg-green-100 text-green-800 hover:bg-green-100",
        status === "pending_approval" &&
          "bg-yellow-100 text-yellow-800 hover:bg-yellow-100",
      )}
    >
      {config.label}
    </Badge>
  );
}
