import { Navigate, Outlet } from "react-router-dom";
import { useIsAuthenticated } from "@azure/msal-react";
import { useSessionStore } from "../store/session";
import { isEntraEnabled } from "../config/msal";

function LocalProtectedRoute() {
  const user = useSessionStore((state) => state.user);
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function EntraProtectedRoute() {
  const user = useSessionStore((state) => state.user);
  const isAuthenticated = useIsAuthenticated();
  if (!user && !isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

export const ProtectedRoute = isEntraEnabled ? EntraProtectedRoute : LocalProtectedRoute;
