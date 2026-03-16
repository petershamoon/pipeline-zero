import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

import { listAuditEvents } from "@/services/audit";
import type { AuditEvent } from "@/types/api";

const PAGE_SIZE = 20;

const actionOptions = [
  { value: "", label: "All Actions" },
  { value: "create", label: "Create" },
  { value: "update", label: "Update" },
  { value: "delete", label: "Delete" },
  { value: "status_change", label: "Status Change" },
  { value: "upload", label: "Upload" },
  { value: "approve", label: "Approve" },
  { value: "reject", label: "Reject" },
  { value: "login", label: "Login" },
  { value: "logout", label: "Logout" },
];

const actionVariant: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  create: "default",
  update: "secondary",
  delete: "destructive",
  status_change: "outline",
  upload: "secondary",
  approve: "default",
  reject: "destructive",
  login: "outline",
  logout: "outline",
};

const columnHelper = createColumnHelper<AuditEvent>();

export function AuditLogPage() {
  const [actionFilter, setActionFilter] = useState("");
  const [page, setPage] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ["audit-events", actionFilter, page],
    queryFn: () =>
      listAuditEvents({
        action: actionFilter || undefined,
        skip: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      }),
  });

  const events = data?.items ?? [];
  const total = data?.total ?? 0;

  const columns = [
    columnHelper.accessor("created_at", {
      header: "Timestamp",
      cell: (info) => {
        const val = info.getValue();
        return val ? new Date(val).toLocaleString() : "--";
      },
    }),
    columnHelper.accessor("actor_id", {
      header: "Actor ID",
      cell: (info) => {
        const val = info.getValue();
        return val ? (
          <span className="font-mono text-xs">{val.slice(0, 8)}...</span>
        ) : (
          <span className="text-muted-foreground">System</span>
        );
      },
    }),
    columnHelper.accessor("action", {
      header: "Action",
      cell: (info) => {
        const action = info.getValue();
        return (
          <Badge variant={actionVariant[action] ?? "outline"}>
            {action}
          </Badge>
        );
      },
    }),
    columnHelper.accessor("resource_type", {
      header: "Resource Type",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("resource_id", {
      header: "Resource ID",
      cell: (info) => (
        <span className="font-mono text-xs">
          {info.getValue().slice(0, 8)}...
        </span>
      ),
    }),
  ];

  const table = useReactTable({
    data: events,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-medium">Audit Log</h2>
        <div className="flex items-center gap-2">
          <Select
            value={actionFilter}
            onValueChange={(val) => {
              setActionFilter(val ?? "");
              setPage(0);
            }}
          >
            <SelectTrigger className="w-44">
              <SelectValue placeholder="All Actions" />
            </SelectTrigger>
            <SelectContent>
              {actionOptions.map((opt) => (
                <SelectItem key={opt.value || "__all"} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : (
        <>
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
                      No audit events found.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {events.length} of {total} events
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page + 1}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={events.length < PAGE_SIZE}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
