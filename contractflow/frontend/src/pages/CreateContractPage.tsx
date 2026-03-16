import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";

import { createContract } from "@/services/contracts";
import { useSessionStore } from "@/store/session";
import {
  createContractSchema,
  type CreateContractFormValues,
} from "@/lib/validations/contract";

export function CreateContractPage() {
  const navigate = useNavigate();
  const user = useSessionStore((state) => state.user);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateContractFormValues>({
    resolver: zodResolver(createContractSchema),
    defaultValues: {
      title: "",
      contract_number: "",
      description: "",
      start_date: "",
      end_date: "",
      value_usd: 0,
      renewal_notice_days: 30,
    },
  });

  const mutation = useMutation({
    mutationFn: (values: CreateContractFormValues) =>
      createContract({
        ...values,
        owner_id: user?.id ?? "",
        department_id: user?.department_id ?? "",
      }),
    onSuccess: (contract) => {
      toast.success("Contract created successfully");
      navigate(`/contracts/${contract.id}`);
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to create contract");
    },
  });

  const onSubmit = (values: CreateContractFormValues) => {
    mutation.mutate(values);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle>Create New Contract</CardTitle>
          <CardDescription>
            Fill in the details below to create a new contract.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                placeholder="Contract title"
                {...register("title")}
                aria-invalid={!!errors.title}
              />
              {errors.title && (
                <p className="text-sm text-destructive">
                  {errors.title.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="contract_number">Contract Number</Label>
              <Input
                id="contract_number"
                placeholder="e.g. CNT-2024-001"
                {...register("contract_number")}
                aria-invalid={!!errors.contract_number}
              />
              {errors.contract_number && (
                <p className="text-sm text-destructive">
                  {errors.contract_number.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Optional description"
                {...register("description")}
                aria-invalid={!!errors.description}
              />
              {errors.description && (
                <p className="text-sm text-destructive">
                  {errors.description.message}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start_date">Start Date</Label>
                <Input
                  id="start_date"
                  type="date"
                  {...register("start_date")}
                  aria-invalid={!!errors.start_date}
                />
                {errors.start_date && (
                  <p className="text-sm text-destructive">
                    {errors.start_date.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="end_date">End Date</Label>
                <Input
                  id="end_date"
                  type="date"
                  {...register("end_date")}
                  aria-invalid={!!errors.end_date}
                />
                {errors.end_date && (
                  <p className="text-sm text-destructive">
                    {errors.end_date.message}
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="value_usd">Value (USD)</Label>
                <Input
                  id="value_usd"
                  type="number"
                  step="0.01"
                  min="0"
                  {...register("value_usd", { valueAsNumber: true })}
                  aria-invalid={!!errors.value_usd}
                />
                {errors.value_usd && (
                  <p className="text-sm text-destructive">
                    {errors.value_usd.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="renewal_notice_days">
                  Renewal Notice (days)
                </Label>
                <Input
                  id="renewal_notice_days"
                  type="number"
                  min="0"
                  {...register("renewal_notice_days", { valueAsNumber: true })}
                  aria-invalid={!!errors.renewal_notice_days}
                />
                {errors.renewal_notice_days && (
                  <p className="text-sm text-destructive">
                    {errors.renewal_notice_days.message}
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate(-1)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || mutation.isPending}>
                {mutation.isPending ? "Creating..." : "Create Contract"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
