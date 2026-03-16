import { http } from "./http";
import type { AuditEventListResponse } from "../types/api";

export async function listAuditEvents(params?: {
  contract_id?: string;
  actor_id?: string;
  action?: string;
  skip?: number;
  limit?: number;
}): Promise<AuditEventListResponse> {
  const { data } = await http.get<AuditEventListResponse>("/audit", {
    params,
  });
  return data;
}
