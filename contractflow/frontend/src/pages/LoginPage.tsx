import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/auth";
import { useSessionStore } from "../store/session";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const setUser = useSessionStore((state) => state.setUser);
  const navigate = useNavigate();

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(email, password);
      setUser(user);
      navigate("/dashboard");
    } catch {
      setError("Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "linear-gradient(145deg, #e2e8f0, #ffffff)" }}>
      <form onSubmit={onSubmit} style={{ width: 360, padding: 24, borderRadius: 12, background: "#ffffff", boxShadow: "0 16px 40px rgba(15, 23, 42, 0.1)" }}>
        <h1 style={{ marginTop: 0 }}>ContractFlow Login</h1>
        <label htmlFor="email">Email</label>
        <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
        <label htmlFor="password">Password</label>
        <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
        {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ width: "100%" }}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
