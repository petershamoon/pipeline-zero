import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "@/services/auth";
import { useSessionStore } from "@/store/session";
import { isEntraEnabled, msalInstance, loginRequest } from "@/config/msal";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

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
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Button type="submit" disabled={loading} className="w-full">
        {loading ? "Signing in..." : "Sign in"}
      </Button>
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
    <Button
      onClick={handleEntraLogin}
      disabled={loading}
      className="w-full"
    >
      {loading ? "Redirecting..." : "Sign in with Microsoft"}
    </Button>
  );
}

export function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-50">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-xl">ContractFlow Login</CardTitle>
          <CardDescription>Enter your credentials to continue</CardDescription>
        </CardHeader>
        <CardContent>
          {isEntraEnabled && <EntraLoginButton />}
          {!isEntraEnabled && <LocalLoginForm />}
        </CardContent>
      </Card>
    </div>
  );
}
