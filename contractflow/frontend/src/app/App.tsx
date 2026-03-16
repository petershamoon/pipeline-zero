import { lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MsalProvider } from "@azure/msal-react";
import { useEffect, type ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ErrorBoundary } from "react-error-boundary";
import { Toaster } from "@/components/ui/sonner";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/AppShell";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { AdminRoute } from "@/components/AdminRoute";
import { getMe } from "@/services/auth";
import { useSessionStore } from "@/store/session";
import { msalInstance, isEntraEnabled } from "@/config/msal";

const LoginPage = lazy(() => import("@/pages/LoginPage").then((m) => ({ default: m.LoginPage })));
const DashboardPage = lazy(() => import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const ContractsListPage = lazy(() => import("@/pages/ContractsListPage").then((m) => ({ default: m.ContractsListPage })));
const ContractDetailPage = lazy(() => import("@/pages/ContractDetailPage").then((m) => ({ default: m.ContractDetailPage })));
const CreateContractPage = lazy(() => import("@/pages/CreateContractPage").then((m) => ({ default: m.CreateContractPage })));
const AdminLayout = lazy(() => import("@/pages/admin/AdminLayout").then((m) => ({ default: m.AdminLayout })));
const AdminUsersPage = lazy(() => import("@/pages/admin/AdminUsersPage").then((m) => ({ default: m.AdminUsersPage })));
const AdminDepartmentsPage = lazy(() => import("@/pages/admin/AdminDepartmentsPage").then((m) => ({ default: m.AdminDepartmentsPage })));
const AdminTemplatesPage = lazy(() => import("@/pages/admin/AdminTemplatesPage").then((m) => ({ default: m.AdminTemplatesPage })));
const AuditLogPage = lazy(() => import("@/pages/admin/AuditLogPage").then((m) => ({ default: m.AuditLogPage })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: (failureCount, error) => {
        if (error && typeof error === "object" && "status" in error) {
          const status = (error as { status: number }).status;
          if (status === 401 || status === 403 || status === 404) return false;
        }
        return failureCount < 3;
      },
    },
  },
});

function PageSkeleton() {
  return (
    <div className="p-6 space-y-4">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-full max-w-md" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </div>
    </div>
  );
}

function ErrorFallback({ error, resetErrorBoundary }: { error: unknown; resetErrorBoundary: () => void }) {
  const message = error instanceof Error ? error.message : "An unexpected error occurred";
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Something went wrong</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">{message}</p>
          <Button onClick={resetErrorBoundary}>Try again</Button>
        </CardContent>
      </Card>
    </div>
  );
}

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
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-muted-foreground">Completing sign-in...</p>
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
        <ErrorBoundary FallbackComponent={ErrorFallback}>
          <BrowserRouter>
            <SessionBootstrap />
            <Suspense fallback={<PageSkeleton />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/auth/callback" element={<AuthCallback />} />

                <Route element={<ProtectedRoute />}>
                  <Route element={<AppShell />}>
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/contracts" element={<ContractsListPage />} />
                    <Route path="/contracts/new" element={<CreateContractPage />} />
                    <Route path="/contracts/:contractId" element={<ContractDetailPage />} />
                    <Route element={<AdminRoute />}>
                      <Route path="/admin" element={<AdminLayout />}>
                        <Route index element={<Navigate to="/admin/users" replace />} />
                        <Route path="users" element={<AdminUsersPage />} />
                        <Route path="departments" element={<AdminDepartmentsPage />} />
                        <Route path="templates" element={<AdminTemplatesPage />} />
                        <Route path="audit" element={<AuditLogPage />} />
                      </Route>
                    </Route>
                  </Route>
                </Route>

                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Suspense>
          </BrowserRouter>
        </ErrorBoundary>
        <Toaster />
      </QueryClientProvider>
    </MsalWrapper>
  );
}
