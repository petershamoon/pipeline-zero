import { useState } from "react";
import { useForm, useFieldArray } from "react-hook-form";
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
import { Skeleton } from "@/components/ui/skeleton";

import { listTemplates, createTemplate } from "@/services/admin";
import type { ApprovalTemplate } from "@/types/api";
import {
  createTemplateSchema,
  type CreateTemplateFormValues,
} from "@/lib/validations/admin";

const columnHelper = createColumnHelper<ApprovalTemplate>();

export function AdminTemplatesPage() {
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["admin-templates"],
    queryFn: listTemplates,
  });

  const createMutation = useMutation({
    mutationFn: (values: CreateTemplateFormValues) =>
      createTemplate({
        name: values.name,
        description: values.description,
        steps_config: values.steps_config,
        min_approvers: values.min_approvers,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-templates"] });
      toast.success("Template created successfully");
      setDialogOpen(false);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create template");
    },
  });

  const columns = [
    columnHelper.accessor("name", {
      header: "Name",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("description", {
      header: "Description",
      cell: (info) =>
        info.getValue() || (
          <span className="text-muted-foreground">--</span>
        ),
    }),
    columnHelper.accessor("min_approvers", {
      header: "Min Approvers",
      cell: (info) => info.getValue(),
    }),
    columnHelper.accessor("is_active", {
      header: "Active",
      cell: (info) =>
        info.getValue() ? (
          <Badge variant="default" className="bg-green-100 text-green-800">
            Active
          </Badge>
        ) : (
          <Badge variant="destructive">Inactive</Badge>
        ),
    }),
  ];

  const table = useReactTable({
    data: templates,
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
        <h2 className="text-lg font-medium">Approval Templates</h2>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button />}>
            Create Template
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Create Approval Template</DialogTitle>
            </DialogHeader>
            <CreateTemplateForm
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
                  No templates found.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

function CreateTemplateForm({
  onSubmit,
  isPending,
}: {
  onSubmit: (values: CreateTemplateFormValues) => void;
  isPending: boolean;
}) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<CreateTemplateFormValues>({
    resolver: zodResolver(createTemplateSchema),
    defaultValues: {
      name: "",
      description: "",
      min_approvers: 1,
      steps_config: [{ name: "", role: "" }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "steps_config",
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="tpl-name">Name</Label>
        <Input
          id="tpl-name"
          {...register("name")}
          aria-invalid={!!errors.name}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="tpl-description">Description</Label>
        <Input id="tpl-description" {...register("description")} />
      </div>

      <div className="space-y-2">
        <Label htmlFor="tpl-min-approvers">Min Approvers</Label>
        <Input
          id="tpl-min-approvers"
          type="number"
          min="1"
          {...register("min_approvers", { valueAsNumber: true })}
          aria-invalid={!!errors.min_approvers}
        />
        {errors.min_approvers && (
          <p className="text-sm text-destructive">
            {errors.min_approvers.message}
          </p>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Approval Steps</Label>
          <Button
            type="button"
            variant="outline"
            size="xs"
            onClick={() => append({ name: "", role: "" })}
          >
            + Add Step
          </Button>
        </div>
        {errors.steps_config?.root && (
          <p className="text-sm text-destructive">
            {errors.steps_config.root.message}
          </p>
        )}
        {fields.map((field, index) => (
          <div key={field.id} className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground w-6 shrink-0">
              {index + 1}.
            </span>
            <Input
              placeholder="Step name"
              {...register(`steps_config.${index}.name`)}
              aria-invalid={!!errors.steps_config?.[index]?.name}
            />
            <Input
              placeholder="Role (optional)"
              {...register(`steps_config.${index}.role`)}
              className="w-32"
            />
            {fields.length > 1 && (
              <Button
                type="button"
                variant="ghost"
                size="icon-xs"
                onClick={() => remove(index)}
              >
                x
              </Button>
            )}
          </div>
        ))}
      </div>

      <DialogFooter>
        <DialogClose render={<Button variant="outline" />}>
          Cancel
        </DialogClose>
        <Button type="submit" disabled={isPending}>
          {isPending ? "Creating..." : "Create Template"}
        </Button>
      </DialogFooter>
    </form>
  );
}
