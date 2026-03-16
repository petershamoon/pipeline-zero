import { z } from "zod";

export const createUserSchema = z.object({
  email: z.string().min(1, "Email is required").email("Invalid email"),
  display_name: z.string().min(1, "Name is required"),
  role: z.enum(["viewer", "contributor", "approver", "admin", "super_admin"]),
  department_id: z.string().optional(),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
export type CreateUserFormValues = z.infer<typeof createUserSchema>;

export const createDepartmentSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
});
export type CreateDepartmentFormValues = z.infer<
  typeof createDepartmentSchema
>;

export const createTemplateSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  min_approvers: z.number().int().min(1, "At least 1 approver required"),
  steps_config: z
    .array(
      z.object({
        name: z.string().min(1),
        role: z.string().optional(),
      }),
    )
    .min(1, "At least one step required"),
});
export type CreateTemplateFormValues = z.infer<typeof createTemplateSchema>;
