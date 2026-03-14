import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChangeEvent, useState } from "react";
import { useParams } from "react-router-dom";
import { decideApproval, listApprovalChains } from "../services/approvals";
import {
  getContract,
  getVersionDownloadUrl,
  listVersions,
  updateContractStatus,
  uploadVersion,
} from "../services/contracts";

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

  return (
    <section>
      <h2>Contract Detail</h2>
      {!contract && <p>Loading contract...</p>}
      {contract && (
        <>
          <p><strong>{contract.contract_number}</strong> - {contract.title}</p>
          <p>Status: {contract.status}</p>
          <button onClick={() => activateMutation.mutate()} disabled={activateMutation.isPending}>Set Active</button>

          <h3>Versions</h3>
          <input type="file" onChange={onFileChange} />
          <button onClick={onUpload} disabled={!selectedFile || uploadMutation.isPending}>Upload Version</button>
          <ul>
            {versions.map((version) => (
              <li key={version.id}>
                v{version.version_number} - {version.file_name}
                <button onClick={() => openDownload(version.id)}>Download</button>
              </li>
            ))}
          </ul>

          <h3>Approvals</h3>
          <ul>
            {chains.map((chain) => (
              <li key={chain.id}>
                Chain {chain.id} - {chain.status}
                {chain.status === "pending" && (
                  <button onClick={() => approveMutation.mutate(chain.id)} disabled={approveMutation.isPending}>
                    Approve Next Step
                  </button>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
