import { z } from "zod";

export const createContractSchema = z
  .object({
    title: z.string().min(1, "Title is required").max(200),
    contract_number: z
      .string()
      .min(1, "Contract number is required")
      .regex(/^[A-Z0-9-]+$/i, "Must be alphanumeric with dashes"),
    description: z.string().optional(),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().min(1, "End date is required"),
    value_usd: z.number().min(0, "Value must be non-negative"),
    renewal_notice_days: z.number().int().min(0, "Must be non-negative"),
  })
  .refine((data) => new Date(data.end_date) > new Date(data.start_date), {
    message: "End date must be after start date",
    path: ["end_date"],
  });

export type CreateContractFormValues = z.infer<typeof createContractSchema>;
