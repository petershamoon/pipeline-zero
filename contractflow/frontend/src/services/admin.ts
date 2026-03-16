import { http } from "./http";
import type { Department, ApprovalTemplate, User } from "../types/api";

export async function listDepartments(): Promise<Department[]> {
  const { data } = await http.get<Department[]>("/admin/departments");
  return data;
}

export async function createDepartment(payload: {
  name: string;
  description?: string;
}): Promise<Department> {
  const { data } = await http.post<Department>("/admin/departments", payload);
  return data;
}

export async function listUsers(): Promise<User[]> {
  const { data } = await http.get<User[]>("/admin/users");
  return data;
}

export async function createUser(payload: {
  email: string;
  display_name: string;
  role: string;
  department_id?: string;
  password?: string;
}): Promise<User> {
  const { data } = await http.post<User>("/admin/users", payload);
  return data;
}

export async function deactivateUser(userId: string): Promise<User> {
  const { data } = await http.post<User>(`/admin/users/${userId}/deactivate`);
  return data;
}

export async function listTemplates(): Promise<ApprovalTemplate[]> {
  const { data } = await http.get<ApprovalTemplate[]>("/admin/templates");
  return data;
}

export async function createTemplate(payload: {
  name: string;
  description?: string;
  steps_config: Record<string, unknown>[];
  min_approvers: number;
}): Promise<ApprovalTemplate> {
  const { data } = await http.post<ApprovalTemplate>(
    "/admin/templates",
    payload,
  );
  return data;
}
