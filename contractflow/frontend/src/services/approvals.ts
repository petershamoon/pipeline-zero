import { http } from "./http";
import type { ApprovalChain, ApprovalChainListResponse } from "../types/api";

export async function listApprovalChains(contractId?: string): Promise<ApprovalChain[]> {
  const { data } = await http.get<ApprovalChainListResponse>("/approvals/chains", {
    params: contractId ? { contract_id: contractId } : {},
  });
  return data.items;
}

export async function createApprovalChain(contractId: string, templateId: string): Promise<ApprovalChain> {
  const { data } = await http.post<ApprovalChain>("/approvals/chains", {
    contract_id: contractId,
    template_id: templateId,
  });
  return data;
}

export async function decideApproval(chainId: string, decision: "approved" | "rejected", comment?: string): Promise<ApprovalChain> {
  const { data } = await http.post<ApprovalChain>(`/approvals/chains/${chainId}/decision`, { decision, comment });
  return data;
}
