import { useQuery } from "@tanstack/react-query";
import { listContracts } from "@/services/contracts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function DashboardPage() {
  const { data = [], isLoading } = useQuery({ queryKey: ["contracts"], queryFn: listContracts });

  const total = data.length;
  const active = data.filter((c) => c.status === "active").length;
  const pending = data.filter((c) => c.status === "pending_approval").length;
  const draft = data.filter((c) => c.status === "draft").length;
  const expired = data.filter((c) => c.status === "expired").length;

  const stats = [
    { label: "Total Contracts", value: total },
    { label: "Active", value: active },
    { label: "Pending Approval", value: pending },
    { label: "Draft", value: draft },
    { label: "Expired", value: expired },
  ];

  return (
    <section className="space-y-6">
      <h2 className="text-2xl font-semibold tracking-tight">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-4 w-24" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16" />
                </CardContent>
              </Card>
            ))
          : stats.map((stat) => (
              <Card key={stat.label}>
                <CardHeader>
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {stat.label}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
                </CardContent>
              </Card>
            ))}
      </div>
    </section>
  );
}
