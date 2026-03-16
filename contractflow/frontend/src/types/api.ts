export type UserRole = "viewer" | "contributor" | "approver" | "admin" | "super_admin";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: UserRole;
  department_id: string | null;
}

export interface Contract {
  id: string;
  title: string;
  description: string | null;
  contract_number: string;
  status: string;
  start_date: string;
  end_date: string;
  value_usd: string;
  renewal_notice_days: number;
  owner_id: string;
  department_id: string;
  is_deleted: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ContractListResponse {
  items: Contract[];
  total: number;
}

export interface ContractVersion {
  id: string;
  contract_id: string;
  version_number: number;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  sha256_checksum: string;
  blob_path: string;
  uploaded_by_id: string;
  created_at: string;
}

export interface ContractVersionListResponse {
  items: ContractVersion[];
  total: number;
}

export interface DownloadUrlResponse {
  download_url: string;
  expires_in_seconds: number;
}

export interface ApprovalStep {
  id: string;
  chain_id: string;
  step_order: number;
  approver_id: string | null;
  decision: "pending" | "approved" | "rejected";
  decided_at: string | null;
  comment: string | null;
}

export interface ApprovalChain {
  id: string;
  contract_id: string;
  template_id: string;
  status: "pending" | "approved" | "rejected" | "cancelled";
  steps: ApprovalStep[];
}

export interface ApprovalChainListResponse {
  items: ApprovalChain[];
  total: number;
}

export interface Department {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface ApprovalTemplate {
  id: string;
  name: string;
  description: string | null;
  steps_config: Record<string, unknown>[];
  min_approvers: number;
  is_active: boolean;
}

export interface AuditEvent {
  id: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  contract_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  correlation_id: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
}

export interface AuditEventListResponse {
  items: AuditEvent[];
  total: number;
}
