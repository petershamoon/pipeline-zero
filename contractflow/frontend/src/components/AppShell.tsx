import { Link, Outlet, useNavigate } from "react-router-dom";
import { logout } from "@/services/auth";
import { useSessionStore } from "@/store/session";
import { buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

export function AppShell() {
  const user = useSessionStore((state) => state.user);
  const setUser = useSessionStore((state) => state.setUser);
  const navigate = useNavigate();

  async function onLogout() {
    await logout();
    setUser(null);
    navigate("/login");
  }

  const isAdmin = user?.role === "admin" || user?.role === "super_admin";

  return (
    <div className="bg-slate-50 min-h-screen font-sans">
      <header className="flex items-center justify-between px-6 py-3 bg-slate-900 text-white">
        <nav className="flex items-center gap-1">
          <Link
            to="/dashboard"
            className="text-sm font-medium text-slate-300 hover:text-white transition-colors px-3 py-1.5 rounded-md hover:bg-slate-800"
          >
            Dashboard
          </Link>
          <Link
            to="/contracts"
            className="text-sm font-medium text-slate-300 hover:text-white transition-colors px-3 py-1.5 rounded-md hover:bg-slate-800"
          >
            Contracts
          </Link>
          {isAdmin && (
            <Link
              to="/admin"
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors px-3 py-1.5 rounded-md hover:bg-slate-800"
            >
              Admin
            </Link>
          )}
          <Link
            to="/contracts/new"
            className={cn(buttonVariants({ size: "sm" }), "ml-2")}
          >
            New Contract
          </Link>
        </nav>

        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors outline-none cursor-pointer">
            {user?.display_name ?? "User"}
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" sideOffset={8}>
            <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onSelect={onLogout}>
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </header>

      <main className="p-6">
        <Outlet />
      </main>
    </div>
  );
}
