import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Outlet, useNavigate, useLocation } from "react-router-dom";

export function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const afterAdmin = location.pathname.split("/admin/")[1] || "users";
  const activeTab = afterAdmin.split("/")[0];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        Administration
      </h1>
      <Tabs
        value={activeTab}
        onValueChange={(v) => navigate(`/admin/${v}`)}
      >
        <TabsList>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="departments">Departments</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>
      </Tabs>
      <Outlet />
    </div>
  );
}
