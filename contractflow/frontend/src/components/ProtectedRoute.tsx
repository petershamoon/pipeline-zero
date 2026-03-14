import { Navigate, Outlet } from "react-router-dom";
import { useSessionStore } from "../store/session";

export function ProtectedRoute() {
  const user = useSessionStore((state) => state.user);
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}
