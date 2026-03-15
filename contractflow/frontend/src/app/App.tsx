import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MsalProvider } from "@azure/msal-react";
import { useEffect, type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ContractDetailPage } from "../pages/ContractDetailPage";
import { ContractsListPage } from "../pages/ContractsListPage";
import { getMe } from "../services/auth";
import { useSessionStore } from "../store/session";
import { msalInstance, isEntraEnabled } from "../config/msal";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

function SessionBootstrap() {
  const setUser = useSessionStore((state) => state.setUser);

  useEffect(() => {
    async function loadSession() {
      try {
        if (isEntraEnabled) {
          await msalInstance.initialize();
          await msalInstance.handleRedirectPromise();
          const accounts = msalInstance.getAllAccounts();
          if (accounts.length === 0) {
            setUser(null);
            return;
          }
        }
        const user = await getMe();
        setUser(user);
      } catch {
        setUser(null);
      }
    }
    void loadSession();
  }, [setUser]);

  return null;
}

function AuthCallback() {
  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center" }}>
      <p>Completing sign-in...</p>
    </div>
  );
}

function MsalWrapper({ children }: { children: ReactNode }) {
  if (isEntraEnabled) {
    return <MsalProvider instance={msalInstance}>{children}</MsalProvider>;
  }
  return <>{children}</>;
}

export function App() {
  return (
    <MsalWrapper>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <SessionBootstrap />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/callback" element={<AuthCallback />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<AppShell />}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/contracts" element={<ContractsListPage />} />
                <Route path="/contracts/:contractId" element={<ContractDetailPage />} />
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </MsalWrapper>
  );
}
