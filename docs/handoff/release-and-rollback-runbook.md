# Release And Rollback Runbook

Last updated: 2026-03-16

## Ownership
- Codex/Claude: code changes, tests, and workflow logic.
- Manus: Azure environment config, identity wiring, release approvals, runtime operations.

## Pipelines used
- CI: `.github/workflows/ci.yml`
- Security gate: `.github/workflows/security.yml`
- Staging deploy: `.github/workflows/deploy-staging.yml`
- Production deploy: `.github/workflows/deploy-production.yml`
- DAST gate: `.github/workflows/dast.yml`

## Staging release flow
1. Merge PR into `main` with required checks green.
2. CI and security workflows complete successfully.
3. Staging deploy workflow runs via OIDC login and updates backend/frontend Container Apps.
4. Run migrations and health checks (`/health/live`, `/health/ready`, frontend `/health`).
5. Execute DAST baseline against staging URL.
6. Mark staging release `READY`.

## Production release flow
1. Confirm staging `READY` and no unresolved high-severity findings.
2. Manual approval in GitHub `production` environment.
3. Deploy production revision.
4. Verify health, smoke tests, and alert quiet period.

## Rollback triggers
- Elevated 5xx error rate post-release.
- Auth failures indicating token validation mismatch.
- Critical data-path failures.
- Job execution regression creating business-state risk.

## Rollback procedure
1. Shift traffic to previous known-good revision.
2. Disable failing scheduled job if needed.
3. Restore impacted secrets/config when contract values changed.
4. Re-run smoke tests on restored revision.
5. Open incident report with timeline and corrective actions.

## Release readiness checklist
- Migration strategy validated (`alembic upgrade head` and rollback path documented).
- Required secrets exist in target Key Vault and GitHub environment.
- Entra role mappings and redirect URIs verified.
- Dashboards/alerts healthy.
- On-call owner confirmed for release window.

## Open items
- ~~`BLOCKED` (Owner: Manus, Due: 2026-03-15): populate GitHub environment secrets for staging and production deploy workflows.~~ **RESOLVED** 2026-03-15 — Staging environment secrets populated and deploy workflow passing. Production environment secrets deferred (production not provisioned).
- ~~`BLOCKED` (Owner: Manus, Due: 2026-03-22): complete first staging dry-run and record release evidence.~~ **RESOLVED** 2026-03-16 — Staging deploy and DAST gate both executed successfully. CI, security-gate, and deploy-staging all green.

## Production status
Production Azure resources are **not provisioned**. The `deploy-production.yml` workflow and Terraform production variable files exist and are ready, but production provisioning has been deferred. Staging is the active demo environment.
