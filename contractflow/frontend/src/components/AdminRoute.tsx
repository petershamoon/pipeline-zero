import { Navigate, Outlet } from "react-router-dom";
import { useIsAdmin } from "@/hooks/useAuthorization";

export function AdminRoute() {
  const isAdmin = useIsAdmin();
  if (!isAdmin) return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}
