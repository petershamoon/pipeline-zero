# Azure Handoff Package (Codex/Claude -> Manus)

Last updated: 2026-03-08
Handoff version: `handoff-2026-03-08`

This folder is the implementation contract for all Azure work.

## Ownership
- Codex/Claude: defines required cloud interfaces and expected runtime behavior.
- Manus: provisions and operates Azure resources to satisfy this contract.

## Files
1. [azure-resource-contract.md](./azure-resource-contract.md)
2. [env-vars-and-secrets-matrix.md](./env-vars-and-secrets-matrix.md)
3. [identity-and-access-matrix.md](./identity-and-access-matrix.md)
4. [network-and-ingress-spec.md](./network-and-ingress-spec.md)
5. [observability-and-alerts-spec.md](./observability-and-alerts-spec.md)
6. [release-and-rollback-runbook.md](./release-and-rollback-runbook.md)

## Definition Of Ready For Manus
- All required rows include concrete values, source of truth, and validation checks.
- Staging and production behavior is explicitly separated.
- Unresolved values are marked `BLOCKED` with owner and due date.

## Current block list
- `BLOCKED` (Owner: Manus, Due: 2026-03-15): final Azure resource names from `terraform apply` outputs.
- `BLOCKED` (Owner: Manus, Due: 2026-03-15): Entra app registration IDs and redirect URIs.
- `BLOCKED` (Owner: Manus, Due: 2026-03-15): GitHub OIDC federated credential subject mappings using actual repo slug.
