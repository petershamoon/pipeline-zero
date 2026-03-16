import { useSessionStore } from "@/store/session";

export function useIsAdmin(): boolean {
  const user = useSessionStore((state) => state.user);
  return user?.role === "admin" || user?.role === "super_admin";
}

export function useCanApprove(): boolean {
  const user = useSessionStore((state) => state.user);
  return (
    user?.role === "approver" ||
    user?.role === "admin" ||
    user?.role === "super_admin"
  );
}

export function useCanEdit(contract: {
  owner_id: string;
  department_id: string;
}): boolean {
  const user = useSessionStore((state) => state.user);
  if (!user) return false;
  if (user.role === "admin" || user.role === "super_admin") return true;
  if (user.role === "viewer") return false;
  return (
    user.id === contract.owner_id ||
    user.department_id === contract.department_id
  );
}
