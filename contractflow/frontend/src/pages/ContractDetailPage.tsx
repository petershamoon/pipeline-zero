import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChangeEvent, useState } from "react";
import { useParams } from "react-router-dom";
import { decideApproval, listApprovalChains } from "@/services/approvals";
import {
  getContract,
  getVersionDownloadUrl,
  listVersions,
  updateContractStatus,
  uploadVersion,
} from "@/services/contracts";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

function statusBadgeVariant(status: string): BadgeVariant {
  switch (status) {
    case "draft":
      return "outline";
    case "pending_approval":
      return "secondary";
    case "active":
      return "default";
    case "expired":
      return "destructive";
    case "terminated":
      return "secondary";
    default:
      return "outline";
  }
}

function formatStatusLabel(status: string): string {
  return status.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatUsd(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (isNaN(num)) return "$0.00";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(num);
}

function formatDate(date: string | null | undefined): string {
  if (!date) return "-";
  return new Date(date).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function ContractDetailPage() {
  const { contractId = "" } = useParams();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const queryClient = useQueryClient();

  const contractQuery = useQuery({
    queryKey: ["contract", contractId],
    queryFn: () => getContract(contractId),
    enabled: Boolean(contractId),
  });

  const versionsQuery = useQuery({
    queryKey: ["versions", contractId],
    queryFn: () => listVersions(contractId),
    enabled: Boolean(contractId),
  });

  const chainQuery = useQuery({
    queryKey: ["approval-chains", contractId],
    queryFn: () => listApprovalChains(contractId),
    enabled: Boolean(contractId),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadVersion(contractId, file),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["versions", contractId] });
    },
  });

  const activateMutation = useMutation({
    mutationFn: () => updateContractStatus(contractId, "active"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["contract", contractId] });
      await queryClient.invalidateQueries({ queryKey: ["contracts"] });
    },
  });

  const approveMutation = useMutation({
    mutationFn: (chainId: string) => decideApproval(chainId, "approved", "Approved from UI"),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["approval-chains", contractId] });
      await queryClient.invalidateQueries({ queryKey: ["contract", contractId] });
    },
  });

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
  }

  async function onUpload() {
    if (!selectedFile) {
      return;
    }
    await uploadMutation.mutateAsync(selectedFile);
    setSelectedFile(null);
  }

  async function openDownload(versionId: string) {
    const download = await getVersionDownloadUrl(contractId, versionId);
    window.open(download.download_url, "_blank");
  }

  const contract = contractQuery.data;
  const versions = versionsQuery.data ?? [];
  const chains = chainQuery.data ?? [];

  if (contractQuery.isLoading) {
    return (
      <section className="space-y-6">
        <Skeleton className="h-8 w-64" />
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-48" />
          </CardHeader>
          <CardContent className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-32" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-4 w-full" />
          </CardContent>
        </Card>
      </section>
    );
  }

  if (!contract) {
    return (
      <section className="space-y-6">
        <p className="text-muted-foreground">Contract not found.</p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            {contract.contract_number}
          </h2>
          <p className="text-muted-foreground">{contract.title}</p>
        </div>
        <Badge variant={statusBadgeVariant(contract.status)}>
          {formatStatusLabel(contract.status)}
        </Badge>
      </div>

      {/* Contract Info */}
      <Card>
        <CardHeader>
          <CardTitle>Contract Information</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Description</dt>
              <dd className="text-sm">{contract.description || "No description"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Value</dt>
              <dd className="text-sm">{formatUsd(contract.value_usd)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Start Date</dt>
              <dd className="text-sm">{formatDate(contract.start_date)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">End Date</dt>
              <dd className="text-sm">{formatDate(contract.end_date)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Renewal Notice</dt>
              <dd className="text-sm">{contract.renewal_notice_days} days</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Version</dt>
              <dd className="text-sm">{contract.version}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Created</dt>
              <dd className="text-sm">{formatDate(contract.created_at)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Updated</dt>
              <dd className="text-sm">{formatDate(contract.updated_at)}</dd>
            </div>
          </dl>
          <Separator className="my-4" />
          <div className="flex gap-2">
            <Button
              onClick={() => activateMutation.mutate()}
              disabled={activateMutation.isPending || contract.status === "active"}
            >
              {activateMutation.isPending ? "Updating..." : "Set Active"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Versions */}
      <Card>
        <CardHeader>
          <CardTitle>Versions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-3">
            <input
              type="file"
              onChange={onFileChange}
              className="text-sm file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-primary-foreground hover:file:bg-primary/90 file:cursor-pointer"
            />
            <Button
              onClick={onUpload}
              disabled={!selectedFile || uploadMutation.isPending}
              variant="outline"
              size="sm"
            >
              {uploadMutation.isPending ? "Uploading..." : "Upload Version"}
            </Button>
          </div>
          {versions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No versions uploaded yet.</p>
          ) : (
            <ul className="space-y-2">
              {versions.map((version) => (
                <li
                  key={version.id}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <div>
                    <span className="text-sm font-medium">
                      v{version.version_number}
                    </span>
                    <span className="text-sm text-muted-foreground ml-2">
                      {version.file_name}
                    </span>
                    <span className="text-xs text-muted-foreground ml-2">
                      ({formatBytes(version.file_size_bytes)})
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openDownload(version.id)}
                  >
                    Download
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Approvals */}
      <Card>
        <CardHeader>
          <CardTitle>Approvals</CardTitle>
        </CardHeader>
        <CardContent>
          {chains.length === 0 ? (
            <p className="text-sm text-muted-foreground">No approval chains.</p>
          ) : (
            <ul className="space-y-3">
              {chains.map((chain) => (
                <li
                  key={chain.id}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">
                      Chain {chain.id.slice(0, 8)}
                    </span>
                    <Badge variant={chain.status === "approved" ? "default" : chain.status === "rejected" ? "destructive" : "outline"}>
                      {formatStatusLabel(chain.status)}
                    </Badge>
                  </div>
                  {chain.status === "pending" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => approveMutation.mutate(chain.id)}
                      disabled={approveMutation.isPending}
                    >
                      {approveMutation.isPending ? "Approving..." : "Approve Next Step"}
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
