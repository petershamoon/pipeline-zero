import { useQuery } from "@tanstack/react-query";
import { listContracts } from "../services/contracts";

export function DashboardPage() {
  const { data = [] } = useQuery({ queryKey: ["contracts"], queryFn: listContracts });

  const active = data.filter((contract) => contract.status === "active").length;
  const pending = data.filter((contract) => contract.status === "pending_approval").length;

  return (
    <section>
      <h2>Dashboard</h2>
      <div style={{ display: "flex", gap: 12 }}>
        <div style={{ padding: 16, background: "#fff", borderRadius: 10 }}>Total contracts: {data.length}</div>
        <div style={{ padding: 16, background: "#fff", borderRadius: 10 }}>Active: {active}</div>
        <div style={{ padding: 16, background: "#fff", borderRadius: 10 }}>Pending approval: {pending}</div>
      </div>
    </section>
  );
}
