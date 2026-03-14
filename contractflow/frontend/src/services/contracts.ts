import { http } from "./http";
import type {
  Contract,
  ContractListResponse,
  ContractVersion,
  ContractVersionListResponse,
  DownloadUrlResponse,
} from "../types/api";

export async function listContracts(): Promise<Contract[]> {
  const { data } = await http.get<ContractListResponse>("/contracts");
  return data.items;
}

export async function getContract(contractId: string): Promise<Contract> {
  const { data } = await http.get<Contract>(`/contracts/${contractId}`);
  return data;
}

export async function createContract(payload: {
  title: string;
  description?: string;
  contract_number: string;
  start_date: string;
  end_date: string;
  value_usd: number;
  renewal_notice_days: number;
  owner_id: string;
  department_id: string;
}): Promise<Contract> {
  const { data } = await http.post<Contract>("/contracts", payload);
  return data;
}

export async function updateContractStatus(contractId: string, status: string): Promise<Contract> {
  const { data } = await http.post<Contract>(`/contracts/${contractId}/status`, { status });
  return data;
}

export async function listVersions(contractId: string): Promise<ContractVersion[]> {
  const { data } = await http.get<ContractVersionListResponse>(`/contracts/${contractId}/versions`);
  return data.items;
}

export async function uploadVersion(contractId: string, file: File): Promise<ContractVersion> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await http.post<ContractVersion>(`/contracts/${contractId}/versions`, form, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export async function getVersionDownloadUrl(contractId: string, versionId: string): Promise<DownloadUrlResponse> {
  const { data } = await http.get<DownloadUrlResponse>(`/contracts/${contractId}/versions/${versionId}/download`);
  return data;
}
