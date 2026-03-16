import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

import { listUsers, createUser, deactivateUser } from "@/services/admin";
import { listDepartments } from "@/services/admin";
import type { User, Department } from "@/types/api";
import {
  createUserSchema,
  type CreateUserFormValues,
} from "@/lib/validations/admin";

const columnHelper = createColumnHelper<User>();

const roleLabels: Record<string, string> = {
  viewer: "Viewer",
  contributor: "Contributor",
  approver: "Approver",
  admin: "Admin",
  super_admin: "Super Admin",
};

export function AdminUsersPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: users = [], isLoading } = useQuery({
    queryKey: ["admin-users"],
    queryFn: listUsers,
  });

  const { data: departments = [] } = useQuery({
    queryKey: ["admin-departments"],
    queryFn: listDepartments,
  });

  const departmentMap = new Map<string, Department>(
    departments.map((d) => [d.id, d]),
  );

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User created successfully");
      setDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create user");
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      toast.success("User deactivated");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to deactivate user");
    },
  });

  const columns = [
    columnHelper.accessor("email", {
      header: "Email",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("display_name", {
      header: "Display Name",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("role", {
      header: "Role",
      cell: (info) => (
        <Badge variant="secondary">
          {roleLabels[info.getValue()] ?? info.getValue()}
        </Badge>
      ),
    }),
    columnHelper.accessor("department_id", {
      header: "Department",
      cell: (info) => {
        const depId = info.getValue();
        if (!depId) return <span className="text-muted-foreground">--</span>;
        return departmentMap.get(depId)?.name ?? depId;
      },
    }),
    columnHelper.display({
      id: "is_active",
      header: "Active",
      cell: ({ row }) => {
        const user = row.original;
        // User type doesn't have is_active; admin endpoint returns it.
        // Cast to get the extended shape from the admin response.
        const isActive = (user as User & { is_active?: boolean }).is_active;
        return isActive !== false ? (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Active
          </Badge>
        ) : (
          <Badge variant="destructive">Inactive</Badge>
        );
      },
    }),
    columnHelper.display({
      id: "actions",
      header: "",
      cell: ({ row }) => {
        const user = row.original;
        const isActive = (user as User & { is_active?: boolean }).is_active;
        if (isActive === false) return null;
        return (
          <AlertDialog>
            <AlertDialogTrigger
              render={
                <Button variant="destructive" size="xs" />
              }
            >
              Deactivate
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Deactivate User</AlertDialogTitle>
                <AlertDialogDescription>
                  Are you sure you want to deactivate {user.email}? They will
                  no longer be able to log in.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  variant="destructive"
                  onClick={() => deactivateMutation.mutate(user.id)}
                >
                  Deactivate
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        );
      },
    }),
  ];

  const table = useReactTable({
    data: users,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">Users</h2>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button />}>Create User</DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Create New User</DialogTitle>
            </DialogHeader>
            <CreateUserForm
              departments={departments}
              onSubmit={(values) => createMutation.mutate(values)}
              isPending={createMutation.isPending}
            />
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext(),
                        )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext(),
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No users found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function CreateUserForm({
  departments,
  onSubmit,
  isPending,
}: {
  departments: Department[];
  onSubmit: (values: CreateUserFormValues) => void;
  isPending: boolean;
}) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: "",
      display_name: "",
      role: "viewer",
      department_id: "",
      password: "",
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="user-email">Email</Label>
        <Input
          id="user-email"
          type="email"
          {...register("email")}
          aria-invalid={!!errors.email}
        />
        {errors.email && (
          <p className="text-sm text-destructive">{errors.email.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="user-display-name">Display Name</Label>
        <Input
          id="user-display-name"
          {...register("display_name")}
          aria-invalid={!!errors.display_name}
        />
        {errors.display_name && (
          <p className="text-sm text-destructive">
            {errors.display_name.message}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Role</Label>
        <Controller
          control={control}
          name="role"
          render={({ field }) => (
            <Select
              value={field.value}
              onValueChange={(val) => field.onChange(val)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="viewer">Viewer</SelectItem>
                <SelectItem value="contributor">Contributor</SelectItem>
                <SelectItem value="approver">Approver</SelectItem>
                <SelectItem value="admin">Admin</SelectItem>
                <SelectItem value="super_admin">Super Admin</SelectItem>
              </SelectContent>
            </Select>
          )}
        />
        {errors.role && (
          <p className="text-sm text-destructive">{errors.role.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label>Department</Label>
        <Controller
          control={control}
          name="department_id"
          render={({ field }) => (
            <Select
              value={field.value ?? ""}
              onValueChange={(val) => field.onChange(val || undefined)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="No department" />
              </SelectTrigger>
              <SelectContent>
                {departments.map((dept) => (
                  <SelectItem key={dept.id} value={dept.id}>
                    {dept.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="user-password">Password</Label>
        <Input
          id="user-password"
          type="password"
          {...register("password")}
          aria-invalid={!!errors.password}
        />
        {errors.password && (
          <p className="text-sm text-destructive">
            {errors.password.message}
          </p>
        )}
      </div>

      <DialogFooter>
        <DialogClose render={<Button variant="outline" />}>
          Cancel
        </DialogClose>
        <Button type="submit" disabled={isPending}>
          {isPending ? "Creating..." : "Create User"}
        </Button>
      </DialogFooter>
    </form>
  );
}
