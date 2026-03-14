# ContractFlow (PipelineZero)

ContractFlow is a security-focused contract lifecycle platform built as a **modular monolith**.

This repository is designed for coordinated execution by:
- **Codex/Claude**: application code, tests, CI/CD logic, and technical docs.
- **Manus**: Azure provisioning, identity/config wiring, environment operations.

## Source of Truth
- Build plan: [`PipelineZero-ContractFlow-Build-Plan-v2.1.docx`](./PipelineZero-ContractFlow-Build-Plan-v2.1.docx)
- Text version: [`PipelineZero-ContractFlow-Build-Plan-v2.1.txt`](./PipelineZero-ContractFlow-Build-Plan-v2.1.txt)

## Architecture Decisions (ADRs)
- Index: [`docs/architecture/adr/README.md`](./docs/architecture/adr/README.md)
- Modular monolith decision: [`docs/architecture/adr/adr-0001-modular-monolith.md`](./docs/architecture/adr/adr-0001-modular-monolith.md)
- Entra ID production auth: [`docs/architecture/adr/adr-0002-entra-id-production-auth.md`](./docs/architecture/adr/adr-0002-entra-id-production-auth.md)
- External scheduled jobs: [`docs/architecture/adr/adr-0003-external-scheduled-jobs.md`](./docs/architecture/adr/adr-0003-external-scheduled-jobs.md)

## Ownership Split

## Codex/Claude Owns
- Backend and frontend code implementation
- Data model, migrations, tests, security policies
- CI/CD workflow code and branch policy workflows
- Azure handoff contract documentation

## Manus Owns
- Azure resource provisioning and lifecycle operations
- Entra tenant/app registration and role/group setup
- Key Vault secrets and managed identity wiring
- Container Apps runtime and scheduled jobs in Azure
- Observability dashboards/alerts and release approvals

## Required Handoff Package for Manus
All handoff files are in [`docs/handoff`](./docs/handoff):
- [`azure-resource-contract.md`](./docs/handoff/azure-resource-contract.md)
- [`env-vars-and-secrets-matrix.md`](./docs/handoff/env-vars-and-secrets-matrix.md)
- [`identity-and-access-matrix.md`](./docs/handoff/identity-and-access-matrix.md)
- [`network-and-ingress-spec.md`](./docs/handoff/network-and-ingress-spec.md)
- [`observability-and-alerts-spec.md`](./docs/handoff/observability-and-alerts-spec.md)
- [`release-and-rollback-runbook.md`](./docs/handoff/release-and-rollback-runbook.md)

## Governance
- Branch/environment policy: [`docs/governance/branch-protection-and-environment-gates.md`](./docs/governance/branch-protection-and-environment-gates.md)
- PR template: [`.github/pull_request_template.md`](./.github/pull_request_template.md)
- Branch guard workflow: [`.github/workflows/branch-policy.yml`](./.github/workflows/branch-policy.yml)

## Execution Plan
- Detailed backlog and tickets: [`docs/execution/build-execution-plan.md`](./docs/execution/build-execution-plan.md)
- Session-by-session plan: [`docs/execution/session-plan.md`](./docs/execution/session-plan.md)

## Demo Approach
Portfolio demos use recorded real findings captured during normal development (scanner catches, before/after diffs, CI gate failures). No intentionally vulnerable code lives in this repository.

## Implementation Snapshot (2026-03-08)
- Codex/Claude implementation is active under [`contractflow`](./contractflow).
- Backend API, migrations, CI/security/deploy workflows, frontend shell/workflows, and Terraform module contracts are implemented.
- Manus handoff package is updated in [`docs/handoff`](./docs/handoff) with `BLOCKED` owner/due-date items for Azure-side execution.

## Immediate Next Step
Execute Manus-owned staging cloud wiring using the updated handoff package in [`docs/handoff`](./docs/handoff), then run first staging deploy + DAST validation.
