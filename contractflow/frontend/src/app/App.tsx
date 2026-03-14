import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { ProtectedRoute } from "../components/ProtectedRoute";
import { LoginPage } from "../pages/LoginPage";
import { DashboardPage } from "../pages/DashboardPage";
import { ContractDetailPage } from "../pages/ContractDetailPage";
import { ContractsListPage } from "../pages/ContractsListPage";
import { getMe } from "../services/auth";
import { useSessionStore } from "../store/session";

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

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <SessionBootstrap />
        <Routes>
          <Route path="/login" element={<LoginPage />} />

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
  );
}
