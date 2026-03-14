import { http } from "./http";
import type { User } from "../types/api";

export async function login(email: string, password: string): Promise<User> {
  const { data } = await http.post<{ status: string; user: User }>("/auth/login", { email, password });
  return data.user;
}

export async function logout(): Promise<void> {
  await http.post("/auth/logout");
}

export async function getMe(): Promise<User> {
  const { data } = await http.get<User>("/auth/me");
  return data;
}

export async function bootstrapAdmin(email: string, password: string): Promise<User> {
  const { data } = await http.post<User>("/auth/bootstrap-admin", { email, password });
  return data;
}
