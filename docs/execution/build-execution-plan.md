# ContractFlow Build Execution Plan (Detailed)

Date: 2026-03-06
Version: aligned to Build Plan v2.1

## Purpose
Provide an execution-ready backlog with ownership, sequencing, and acceptance criteria.

## Owners
- Codex/Claude: app code, tests, CI/CD logic, handoff documentation.
- Manus: Azure implementation and operational controls.

## Status Snapshot (2026-03-08)
- Completed by Codex/Claude: TKT-001, TKT-002, TKT-003, TKT-004, TKT-005, TKT-006, TKT-007, TKT-009, TKT-010, TKT-011, TKT-012, TKT-013, TKT-014, TKT-015, TKT-017, TKT-018, TKT-019, TKT-020, TKT-021 (workflow side), TKT-023, TKT-024 (documentation baseline).
- Pending Manus-owned execution: TKT-008, TKT-016, TKT-021 (federated credential and role assignment side), TKT-022.
- Validation blockers: first staging deploy and cloud observability acceptance are blocked on Azure configuration and secrets population.

## Labels
- `area:backend`
- `area:frontend`
- `area:security`
- `area:ci-cd`
- `area:infra`
- `owner:codex-claude`
- `owner:manus`

## Milestone M1 - Foundations

### TKT-001 Repo Scaffold and Standards
- Owner: Codex/Claude
- Depends on: none
- Scope:
  - Repository folder structure.
  - Base README and contribution notes.
  - Coding/lint conventions.
- Done criteria:
  - Project tree matches plan.
  - Lint command runs for backend/frontend.

### TKT-002 Local Runtime Baseline
- Owner: Codex/Claude
- Depends on: TKT-001
- Scope:
  - `docker-compose.yml` with backend, frontend, postgres, redis, azurite.
  - Backend `/health/live` and `/health/ready` endpoints.
  - Frontend `/health` endpoint.
- Done criteria:
  - `docker compose up` starts cleanly.
  - Health checks return 200.

### TKT-003 ADR + Handoff Baseline
- Owner: Codex/Claude
- Depends on: TKT-001
- Scope:
  - ADR files for architecture, auth, scheduled jobs.
  - Initial handoff docs for Manus.
- Done criteria:
  - ADRs marked Accepted.
  - All handoff documents exist and are non-placeholder.

## Milestone M2 - Data and Auth

### TKT-004 Data Model and Constraints
- Owner: Codex/Claude
- Depends on: TKT-001
- Scope:
  - SQLAlchemy models and enums.
  - Indexes, check constraints, soft-delete fields.
  - audit field naming conflict avoided (`metadata_json`).
- Done criteria:
  - Model tests pass.
  - Schema review checklist signed.

### TKT-005 Alembic Initial Migration
- Owner: Codex/Claude
- Depends on: TKT-004
- Scope:
  - Alembic setup and initial migration.
  - Migration apply/revert test in local environment.
- Done criteria:
  - `alembic upgrade head` passes from empty DB.
  - Down migration strategy documented.

### TKT-006 Entra Auth Integration (Prod Path)
- Owner: Codex/Claude
- Depends on: TKT-001
- Scope:
  - OIDC validation logic in backend.
  - SPA auth client scaffolding and callback flow.
  - Role claim mapping to app roles.
- Done criteria:
  - Auth integration tests pass with token fixtures.
  - Production startup fails fast if Entra config missing.

### TKT-007 Local Auth Fallback (Dev Only)
- Owner: Codex/Claude
- Depends on: TKT-006
- Scope:
  - Dev-only login for local workflows.
  - Explicit environment guard disabling in production.
- Done criteria:
  - Local login works in development.
  - Production mode rejects fallback path.

### TKT-008 Entra Tenant/App Setup
- Owner: Manus
- Depends on: docs/handoff package
- Scope:
  - App registrations (SPA and API if separated).
  - Redirect URIs and logout URIs.
  - App role/group setup.
- Done criteria:
  - Login works in staging.
  - Claims contain expected role mapping.

## Milestone M3 - Core Domain

### TKT-009 Authorization Policy Library
- Owner: Codex/Claude
- Depends on: TKT-004, TKT-006
- Scope:
  - Centralized role and object-level access checks.
  - Reusable helpers for contract-scoped endpoints.
- Done criteria:
  - Security tests for owner/department/grant/admin paths pass.

### TKT-010 Contract CRUD + Lifecycle
- Owner: Codex/Claude
- Depends on: TKT-009
- Scope:
  - Contract create/list/detail/update/archive endpoints.
  - Lifecycle transitions with validation rules.
- Done criteria:
  - Integration tests for all transitions pass.

### TKT-011 Audit Logging Pipeline
- Owner: Codex/Claude
- Depends on: TKT-010
- Scope:
  - Append-only audit writes for all state changes.
  - Correlation ID support.
- Done criteria:
  - Every mutation endpoint emits audit event.
  - Audit query endpoint supports pagination and filters.

## Milestone M4 - Versions and Approvals

### TKT-012 File Upload and Versioning
- Owner: Codex/Claude
- Depends on: TKT-010
- Scope:
  - MIME allowlist validation.
  - Size checks and checksum storage.
  - Versioned blob path strategy and download URL generation.
- Done criteria:
  - Upload/download integration tests pass.
  - Disallowed files rejected server-side.

### TKT-013 Approval Templates and Chains
- Owner: Codex/Claude
- Depends on: TKT-010
- Scope:
  - Template selection logic.
  - Chain creation and step progression.
  - Reject and override behavior.
- Done criteria:
  - Approvals integration tests cover happy and failure paths.

### TKT-014 Admin APIs
- Owner: Codex/Claude
- Depends on: TKT-009
- Scope:
  - User/department/template admin endpoints.
  - Global audit querying.
- Done criteria:
  - Non-admin denied with tests.

## Milestone M5 - Jobs and UX

### TKT-015 Scheduled Job Containers
- Owner: Codex/Claude
- Depends on: TKT-010, TKT-011
- Scope:
  - Build job entrypoints for expiration and notification tasks.
  - Idempotency and retry-safe behavior.
- Done criteria:
  - Local job execution test runs cleanly.

### TKT-016 Azure Job Scheduling and Identity
- Owner: Manus
- Depends on: TKT-015, handoff docs
- Scope:
  - Container Apps Job creation.
  - Schedules, secrets, and identity bindings.
- Done criteria:
  - Scheduled job executes in staging and logs are visible.

### TKT-017 Frontend Auth and Shell
- Owner: Codex/Claude
- Depends on: TKT-006
- Scope:
  - Login flow, protected routes, role-aware navigation.
  - Session-safe frontend behavior.
- Done criteria:
  - Unauthorized users redirected correctly.

### TKT-018 Frontend Contract Workflows
- Owner: Codex/Claude
- Depends on: TKT-010, TKT-012, TKT-013
- Scope:
  - Dashboard, list, details, upload, versions, approvals.
- Done criteria:
  - End-to-end core workflow passes in staging.

## Milestone M6 - DevSecOps and Release

### TKT-019 CI Lint/Test Gate
- Owner: Codex/Claude
- Depends on: TKT-001 onward
- Scope:
  - Unified CI workflow for lint + tests.
- Done criteria:
  - PR blocked on failing tests.

### TKT-020 Security Gate
- Owner: Codex/Claude
- Depends on: TKT-019
- Scope:
  - Semgrep, CodeQL, Trivy, Checkov, Gitleaks jobs.
  - Branch policy check workflow.
- Done criteria:
  - Critical findings fail PR.

### TKT-021 Azure OIDC Deploy Wiring
- Owner: Codex/Claude + Manus
- Depends on: TKT-020
- Scope:
  - OIDC-based deploy workflows.
  - Federated credentials and role assignments.
- Done criteria:
  - Staging deploy succeeds without static cloud credentials.

### TKT-022 Observability and Alerts
- Owner: Manus
- Depends on: TKT-021, handoff docs
- Scope:
  - Dashboards and alerts from observability spec.
- Done criteria:
  - Synthetic alert tests confirm notification routing.

### TKT-023 DAST Gate
- Owner: Codex/Claude
- Depends on: TKT-021
- Scope:
  - ZAP baseline against staging after deployment.
- Done criteria:
  - DAST job runs and archives report artifact.

## Milestone M7 - Finalization and Portfolio

### TKT-024 Portfolio Demo Pack
- Owner: Codex/Claude
- Depends on: TKT-023
- Scope:
  - Collect recorded real security findings (scanner catches, CI gate failures, before/after diffs).
  - Build repeatable demo walkthrough from real development artifacts.
  - LinkedIn-ready architecture summary.
- Done criteria:
  - Demo walkthrough validated end-to-end using only real recorded findings.

## Execution sequence (recommended)
1. Complete M1, M2, and M3 before heavy frontend work.
2. Parallelize M4/M5 once API contracts stabilize.
3. Start Manus Azure implementation after handoff package freeze.
4. Keep M6 gates mandatory before any production promotion.
5. Finish with M7 for portfolio polish.
