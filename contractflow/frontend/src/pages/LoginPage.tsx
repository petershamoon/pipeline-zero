import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../services/auth";
import { useSessionStore } from "../store/session";
import { isEntraEnabled, msalInstance, loginRequest } from "../config/msal";

function LocalLoginForm() {
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
    <form onSubmit={onSubmit}>
      <label htmlFor="email">Email</label>
      <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
      <label htmlFor="password">Password</label>
      <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%", marginBottom: 12 }} />
      {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
      <button type="submit" disabled={loading} style={{ width: "100%" }}>
        {loading ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
}

function EntraLoginButton() {
  const [loading, setLoading] = useState(false);

  async function handleEntraLogin() {
    setLoading(true);
    try {
      await msalInstance.initialize();
      await msalInstance.loginRedirect(loginRequest);
    } catch {
      setLoading(false);
    }
  }

  return (
    <button
      onClick={handleEntraLogin}
      disabled={loading}
      style={{
        width: "100%",
        padding: "10px 16px",
        backgroundColor: "#0078d4",
        color: "#ffffff",
        border: "none",
        borderRadius: 6,
        cursor: loading ? "wait" : "pointer",
        fontSize: 14,
        fontWeight: 500,
      }}
    >
      {loading ? "Redirecting..." : "Sign in with Microsoft"}
    </button>
  );
}

export function LoginPage() {
  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "linear-gradient(145deg, #e2e8f0, #ffffff)" }}>
      <div style={{ width: 360, padding: 24, borderRadius: 12, background: "#ffffff", boxShadow: "0 16px 40px rgba(15, 23, 42, 0.1)" }}>
        <h1 style={{ marginTop: 0 }}>ContractFlow Login</h1>
        {isEntraEnabled && <EntraLoginButton />}
        {!isEntraEnabled && <LocalLoginForm />}
      </div>
    </div>
  );
}
