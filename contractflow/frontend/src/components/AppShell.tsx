import { Link, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../services/auth";
import { useSessionStore } from "../store/session";

export function AppShell() {
  const user = useSessionStore((state) => state.user);
  const setUser = useSessionStore((state) => state.setUser);
  const navigate = useNavigate();

  async function onLogout() {
    await logout();
    setUser(null);
    navigate("/login");
  }

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', sans-serif", minHeight: "100vh", background: "#f6f8fb" }}>
      <header style={{ display: "flex", justifyContent: "space-between", padding: "16px 24px", background: "#0f172a", color: "#fff" }}>
        <nav style={{ display: "flex", gap: 12 }}>
          <Link style={{ color: "#fff" }} to="/dashboard">Dashboard</Link>
          <Link style={{ color: "#fff" }} to="/contracts">Contracts</Link>
        </nav>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span>{user?.display_name}</span>
          <button onClick={onLogout}>Logout</button>
        </div>
      </header>
      <main style={{ padding: 24 }}>
        <Outlet />
      </main>
    </div>
  );
}
