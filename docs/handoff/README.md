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
- *All initial BLOCKED items resolved by Manus on 2026-03-15.*
- `BLOCKED` (Owner: Pete/Claude, Due: 2026-03-22): Application code needs to implement `/health` and `/health/ready` endpoints for the GitHub Actions smoke tests to pass.
- `BLOCKED` (Owner: Pete/Claude, Due: 2026-03-22): Database migration scripts need to be finalized and run against the staging PostgreSQL instance.
