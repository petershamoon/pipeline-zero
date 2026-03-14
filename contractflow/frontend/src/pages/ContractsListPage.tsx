import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { listContracts } from "../services/contracts";

export function ContractsListPage() {
  const { data = [], isLoading } = useQuery({ queryKey: ["contracts"], queryFn: listContracts });

  return (
    <section>
      <h2>Contracts</h2>
      {isLoading && <p>Loading contracts...</p>}
      <table style={{ width: "100%", borderCollapse: "collapse", background: "#fff" }}>
        <thead>
          <tr>
            <th align="left">Number</th>
            <th align="left">Title</th>
            <th align="left">Status</th>
            <th align="left">End Date</th>
            <th align="left">Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.map((contract) => (
            <tr key={contract.id}>
              <td>{contract.contract_number}</td>
              <td>{contract.title}</td>
              <td>{contract.status}</td>
              <td>{contract.end_date}</td>
              <td>
                <Link to={`/contracts/${contract.id}`}>Open</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
