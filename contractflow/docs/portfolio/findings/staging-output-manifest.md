# ContractFlow Staging — Output Manifest

**Date:** 2026-03-14
**Author:** Manus AI
**Status:** Phases 2–4 Complete; Phases 1, 5–8 Ready for Next Session

---

## Staging Output Manifest (Non-Secret Values Only)

| Category | Property | Value |
|---|---|---|
| **Subscription** | Subscription ID | `5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08` |
| **Subscription** | Tenant ID | `<REDACTED-TENANT-ID>` |
| **Subscription** | Region | `eastus2` |
| **Entra App (Staging)** | Display Name | ContractFlow Staging |
| **Entra App (Staging)** | Application (client) ID | `41c4eaf5-7b36-4b1a-9d17-8d35b9c5e2da` |
| **Entra App (Staging)** | Object ID | `330fa4cd-cc41-471d-b61b-199d07f51e21` |
| **Entra App (Staging)** | Identifier URI | `api://41c4eaf5-7b36-4b1a-9d17-8d35b9c5e2da` |
| **Entra App (Staging)** | SP Object ID | `ffdc7fc0-f4e5-471d-b7d9-ee21f6980105` |
| **Entra App (Staging)** | SPA Redirect URI | `http://localhost:3000/auth/callback` |
| **Entra App (Staging)** | Exposed Scope | `access_as_user` |
| **Entra App (Staging)** | App Roles | Viewer, Contributor, Approver, Admin, SuperAdmin |
| **Entra App (Staging)** | Secret Expiry | 2026-06-14 |
| **OIDC Deploy App** | Display Name | ContractFlow GitHub Deploy |
| **OIDC Deploy App** | Application (client) ID | `5a2dc89a-c874-4b53-ae0b-5f706f82ffe6` |
| **OIDC Deploy App** | Object ID | `62a5465c-4e06-4ebd-8458-d7c2a7cdc8ff` |
| **OIDC Deploy App** | SP Object ID | `89e772b8-71e7-44e9-a1e8-cbd179b711d4` |
| **OIDC Deploy App** | Federated Cred: Staging | `repo:petershamoon/aiuc1-soc2-compliance-lab:environment:staging` |
| **OIDC Deploy App** | Federated Cred: Production | `repo:petershamoon/aiuc1-soc2-compliance-lab:environment:production` |
| **OIDC Deploy App** | Federated Cred: Main | `repo:petershamoon/aiuc1-soc2-compliance-lab:ref:refs/heads/main` |
| **OIDC Deploy App** | Role Assignments | Contributor + User Access Administrator @ subscription |
| **Terraform SP** | Application (client) ID | `8fc64ab2-ee80-4e15-a386-c9ba8650dcaf` |
| **Terraform SP** | SP Object ID | `faa7af0e-f6a7-4c8f-9361-f30d67a62483` |
| **Terraform SP** | Role Assignments | Contributor + User Access Administrator @ subscription |
| **Terraform SP** | Secret Expiry | 2026-06-14 |
| **Resource Names** | Resource Group | `cf-stg-rg-eastus2-01` |
| **Resource Names** | Container Apps Env | `cf-stg-cae-eastus2-01` |
| **Resource Names** | Backend App | `cf-stg-api-eastus2-01` |
| **Resource Names** | Frontend App | `cf-stg-web-eastus2-01` |
| **Resource Names** | Expiration Job | `cf-stg-job-exp-eastus2-01` |
| **Resource Names** | Notification Job | `cf-stg-job-notify-eastus2-01` |
| **Resource Names** | PostgreSQL | `cf-stg-pg-eastus2-01` |
| **Resource Names** | Redis | `cf-stg-redis-eastus2-01` |
| **Resource Names** | Storage Account | `cfstg01sa` |
| **Resource Names** | Key Vault | `cf-stg-kv-eastus2-01` |
| **Resource Names** | ACR | `cfstg01acr` |
| **Resource Names** | Log Analytics | `cf-stg-log-eastus2-01` |
| **Resource Names** | Managed Identity | `cf-stg-id-eastus2-01` |

---

## Validation Evidence

### Phase 2: Entra ID Configuration

| Check | Command | Result |
|---|---|---|
| App exists | `az ad app show --id 41c4eaf5-...` | Confirmed — display name "ContractFlow Staging" |
| Identifier URI | `az ad app show --query identifierUris` | `["api://41c4eaf5-7b36-4b1a-9d17-8d35b9c5e2da"]` |
| SPA redirect | `az ad app show --query spa.redirectUris` | `["http://localhost:3000/auth/callback"]` |
| App roles | `az ad app show --query appRoles[].value` | `["ContractFlow.SuperAdmin","ContractFlow.Admin","ContractFlow.Approver","ContractFlow.Contributor","ContractFlow.Viewer"]` |
| API scope | `az ad app show --query api.oauth2PermissionScopes[].value` | `["access_as_user"]` |
| Client secret | `az ad app credential list --id 41c4eaf5-...` | 1 secret, expires 2026-06-14 |
| Service principal | `az ad sp list --filter "appId eq '41c4eaf5-...'"` | SP ID `ffdc7fc0-f4e5-471d-b7d9-ee21f6980105` |
| Portal screenshot | `2026-03-14-entra-contractflow-staging-overview.webp` | All properties visible |
| Portal screenshot | `2026-03-14-entra-app-roles-configured.webp` | 5 roles, all Enabled |
| Portal screenshot | `2026-03-14-entra-expose-api-scope.webp` | Scope `access_as_user` visible |

### Phase 3: GitHub OIDC Federation

| Check | Command | Result |
|---|---|---|
| OIDC app exists | `az ad app show --id 5a2dc89a-...` | Confirmed — "ContractFlow GitHub Deploy" |
| Fed cred: staging | `az ad app federated-credential list --id 62a5465c-...` | Subject: `repo:petershamoon/aiuc1-soc2-compliance-lab:environment:staging` |
| Fed cred: production | Same | Subject: `...environment:production` |
| Fed cred: main | Same | Subject: `...ref:refs/heads/main` |
| Role: Contributor | `az role assignment list --assignee 89e772b8-...` | Contributor @ subscription scope |
| Role: UAA | Same | User Access Administrator @ subscription scope |
| Portal screenshot | `2026-03-14-github-oidc-federated-credentials.webp` | 3 credentials visible |

### Phase 4: Secrets / .env File

| Check | Command | Result |
|---|---|---|
| .env file exists | `wc -l contractflow/infra/.env.staging` | 97 lines, 50 key-value pairs |
| .gitignore updated | `grep .env.staging .gitignore` | Present in both root and contractflow/ |
| Passwords generated | Verified lengths | PG: 24 chars, DB: 24 chars, CSRF: 64 chars |

---

## Files Changed

| File | Change Summary |
|---|---|
| `contractflow/infra/modules/platform/main.tf` | Rewritten from naming stub to full 13-resource Terraform config |
| `contractflow/infra/variables.tf` | Added 8 new variables for DB creds, Entra config, budget |
| `contractflow/infra/main.tf` | Updated module call to pass new variables |
| `contractflow/infra/outputs.tf` | Added 10+ new outputs for resource IDs, FQDNs, connection strings |
| `contractflow/infra/envs/staging/terraform.tfvars` | Created with staging-specific values |
| `contractflow/infra/.env.staging` | **NEW** — Complete 50+ key-value credential/config file |
| `contractflow/infra/scripts/provision-all-permissions.sh` | **NEW** — Full provisioning script (reference) |
| `contractflow/infra/scripts/01-entra-app-registration.sh` | **NEW** — Entra app setup script |
| `contractflow/infra/scripts/02-github-oidc-federation.sh` | **NEW** — OIDC federation script |
| `contractflow/infra/scripts/03-github-environment-secrets.sh` | **NEW** — GitHub secrets population script |
| `contractflow/infra/scripts/04-post-deploy-validation.sh` | **NEW** — Health check and DAST script |
| `contractflow/infra/scripts/00-run-all.sh` | **NEW** — Master orchestration script |
| `.gitignore` | Added `.env.staging` entries |
| `contractflow/.gitignore` | **NEW** — Added `.env.staging` entries |
| `contractflow/docs/portfolio/findings/staging-implementation-log.md` | Updated with 4 log entries, 7 screenshots, 5 lessons learned |
| `contractflow/docs/portfolio/findings/screenshots/notes.md` | Updated with 7 screenshot entries and captions |

---

## Unresolved Blockers

| Blocker | Owner | Reason | ETA |
|---|---|---|---|
| Terraform apply not yet run | Manus (next session) | Requires `source .env.staging` then `terraform apply` | Next session |
| Key Vault secrets not populated | Manus (next session) | KV doesn't exist yet (created by Terraform) | After Phase 1 |
| GitHub environment secrets not set | Manus (next session) | Can be set now via `gh secret set` but waiting for resource validation | After Phase 1 |
| Container Apps not deployed | Manus (next session) | Requires Terraform resources + Docker images in ACR | After Phase 1 |
| Staging FQDN redirect URI | Manus (next session) | Need to add `https://<staging-fqdn>/auth/callback` to Entra SPA redirects after Container Apps are created | After Phase 5 |
| Observability dashboards | Manus (next session) | Log Analytics workspace created by Terraform; dashboards configured after | After Phase 1 |
| DAST run | Manus (next session) | Requires running staging environment | After Phase 7 |
| Azure credits | Pete | $185.86 remaining, expires March 20, 2026 — may need upgrade for sustained staging | Ongoing |

---

## Next Session Handoff

The next session should read the `contractflow-staging` skill (`/home/ubuntu/skills/contractflow-staging/SKILL.md`) and follow these steps:

1. Source credentials: `source contractflow/infra/.env.staging`
2. Authenticate: `az login --service-principal -u $ARM_CLIENT_ID -p $ARM_CLIENT_SECRET --tenant $ARM_TENANT_ID`
3. Run Terraform: `cd contractflow/infra && terraform apply -var-file=envs/staging/terraform.tfvars`
4. Populate Key Vault secrets after resources are created
5. Set GitHub environment secrets via `gh secret set`
6. Build and push Docker images to ACR
7. Deploy Container Apps and validate health checks
8. Run DAST against staging URLs
9. Update handoff docs with concrete FQDNs and connection info
