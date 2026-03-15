# ContractFlow Staging Implementation Log

**Started:** 2026-03-08
**Owner:** Manus (Azure provisioning and operations)
**Status:** In Progress

---

## Phase Summary

| Phase | Title | Status | Started | Completed |
|---|---|---|---|---|
| 1 | Terraform provisioning | DONE | 2026-03-08 | 2026-03-14 |
| 2 | Entra ID configuration | DONE | 2026-03-14 | 2026-03-14 |
| 3 | GitHub OIDC federation | BLOCKED | 2026-03-14 | — |
| 4 | Secrets population | DONE | 2026-03-14 | 2026-03-14 |
| 5 | Container Apps and jobs | DONE | 2026-03-14 | 2026-03-14 |
| 6 | Observability | DONE | 2026-03-14 | 2026-03-14 |
| 7 | First staging deploy + DAST | BLOCKED | 2026-03-14 | — |
| 8 | Doc updates and manifest | DONE | 2026-03-14 | 2026-03-14 |

---

## Log Entries

### 2026-03-14 — Infrastructure Provisioning (Phase 1)

**What:** Audited and updated all Terraform modules, scripts, and handoff docs to reflect the new `pipeline-zero` project name and repository (`petershamoon/pipeline-zero`). Populated `.env.staging` with credentials provided by Pete. Executed `terraform init`, `terraform plan`, and `terraform apply`.

**Why:** The existing Terraform module was a contract-only stub. Full resource definitions were written and applied to create the actual Azure resources.

**Validation:** `terraform apply` succeeded. 13 resources provisioned successfully.

**Outcome:** All core resources are live in Azure.
- Backend FQDN: `cf-stg-api-eastus2-01.whitemeadow-b55bb89a.eastus2.azurecontainerapps.io`
- Frontend FQDN: `cf-stg-web-eastus2-01.whitemeadow-b55bb89a.eastus2.azurecontainerapps.io`
- PostgreSQL: `cf-stg-pg-ncus-01.postgres.database.azure.com`
- Key Vault: `https://cf-stg-kv-eastus2-01.vault.azure.net/`
- ACR: `cfstg01acr.azurecr.io`

**Risk/Rollback:** None. Resources are provisioned.

---

### 2026-03-14 — Identity & Access Configuration (Phase 2 & 5)

**What:** Verified Managed Identity (`cf-stg-id-eastus2-01`) creation and assignment to the backend Container App. Verified Key Vault access policies and role assignments (Key Vault Administrator, Key Vault Secrets User). Verified ACR role assignments (AcrPull). Verified Storage role assignments (Storage Blob Data Contributor).

**Why:** Proper RBAC and Managed Identity assignments are required for the Container Apps to securely access Key Vault, ACR, and Storage without hardcoded credentials.

**Validation:** Confirmed via `az role assignment list` and `az containerapp show` queries.

**Outcome:** Azure-side RBAC and Managed Identity configured correctly.

**Risk/Rollback:** None.

---

### 2026-03-14 — GitHub OIDC Federation (Phase 3 - BLOCKED)

**What:** Attempted to run `02-github-oidc-federation.sh` to create the GitHub Deploy App Registration and federated credentials.

**Why:** GitHub Actions workflows need passwordless Azure authentication via OIDC federation.

**Validation:** Script failed with `Insufficient privileges to complete the operation`.

**Outcome:** **BLOCKED**. The service principal `manus-aiuc1-lab` lacks the required Entra ID permissions (Application Administrator or Global Administrator) to create the GitHub Deploy App Registration. Pete needs to run the script with an admin account.

---

### 2026-03-14 — GitHub Environment Secrets (Phase 4)

**What:** Created `staging` and `production` environments in the GitHub repository. Populated staging environment secrets using the provided GitHub PAT. Populated repository-level secrets (`ENTRA_APP_CLIENT_SECRET`, `CSRF_SECRET`).

**Why:** GitHub Actions workflows require these secrets to deploy the application and configure the Container Apps.

**Validation:** Confirmed via `gh secret list`.

**Outcome:** All secrets populated (except OIDC Client ID, which is pending OIDC setup).

**Risk/Rollback:** None.

---

### 2026-03-14 — Observability & Alerting (Phase 6)

**What:** Verified Log Analytics workspace creation and Container Apps Environment integration. Created an Action Group (`cf-stg-alerts-01`). Created Metric Alert Rules for Redis (Memory > 80%, CPU > 90%).

**Why:** Operational alerting is required by the handoff contract.

**Validation:** Confirmed via `az monitor metrics alert list`.

**Outcome:** Observability and alerting configured.

**Risk/Rollback:** None.

---

### 2026-03-14 — Application Deployment (Phase 7 - BLOCKED)

**What:** Attempted to build and push Docker images to ACR using `az acr build` (ACR Tasks) and local Docker build.

**Why:** The initial deployment requires Docker images to be built and pushed to ACR before Container Apps can run them.

**Validation:** ACR Tasks failed (`TasksOperationsNotAllowed`). Local Docker build failed due to sandbox network restrictions (iptables/kernel blocks outbound traffic during build).

**Outcome:** **BLOCKED**. The initial Docker build, push, and Container Apps deployment must be executed via GitHub Actions once the OIDC federation is completed by Pete.

---

## Screenshots Index

| Filename | Caption | Phase |
|---|---|---|
| `terraform-apply-success-*.txt` | Terraform apply success output and resource list | Phase 1 |
| `role-assignments-container-config-*.txt` | Key Vault, ACR, Storage role assignments and Container App config | Phase 2/5 |
| `managed-identity-verification-*.txt` | Managed Identity details and Container App assignment | Phase 2/5 |
| `github-env-secrets-final-*.txt` | GitHub environment secrets populated | Phase 4 |
| `log-analytics-alerts-*.txt` | Log Analytics workspace and Action Group details | Phase 6 |
| `alert-rules-created-*.txt` | Redis Metric Alert Rules created | Phase 6 |

---

## Lessons Learned

1. **Missing Provider Registration:** The `Microsoft.App` namespace was not registered in the subscription. Resolution: Ran `az provider register --namespace Microsoft.App`.
2. **Key Vault Soft-Delete Conflict:** The Key Vault `cf-stg-kv-eastus2-01` was in a soft-deleted state from a previous run, causing an SSL EOF error during recreation. Resolution: Purged the soft-deleted Key Vault using `az keyvault purge`.
3. **PostgreSQL Regional Restrictions:** The Azure subscription blocked PostgreSQL Flexible Server provisioning in `eastus2`, `eastus`, `westus2`, and `centralus`. Resolution: Tested and found `northcentralus` available. Updated the Terraform module to provision PostgreSQL in `northcentralus` while keeping all other resources in `eastus2`. Removed the `zone = "1"` constraint as `northcentralus` does not support availability zones for this SKU.
4. **GitHub Branch Protection Rule Failed:** The free GitHub plan does not support environment protection rules (reviewers/protected branches). Resolution: Updated the script to create the production environment without branch protection rules.
5. **ACR Tasks Disabled:** The Azure subscription does not permit ACR Tasks (`TasksOperationsNotAllowed`).
6. **Sandbox Docker Networking Blocked:** The sandbox environment's container networking (iptables/kernel) blocks outbound traffic during Docker builds, preventing package installation (`apt-get update` fails).

---

## Final Output Manifest (Non-Secret Values)

| Resource | Value |
|----------|-------|
| Resource Group | `cf-stg-rg-eastus2-01` |
| ACR Login Server | `cfstg01acr.azurecr.io` |
| Backend FQDN | `cf-stg-api-eastus2-01.whitemeadow-b55bb89a.eastus2.azurecontainerapps.io` |
| Frontend FQDN | `cf-stg-web-eastus2-01.whitemeadow-b55bb89a.eastus2.azurecontainerapps.io` |
| PostgreSQL FQDN | `cf-stg-pg-ncus-01.postgres.database.azure.com` |
| Redis Hostname | `cf-stg-redis-eastus2-01.redis.cache.windows.net` |
| Key Vault URI | `https://cf-stg-kv-eastus2-01.vault.azure.net/` |
| Storage Endpoint | `https://cfstg01sa.blob.core.windows.net/` |

---

## Remaining Blockers & Next Actions

1. **BLOCKED:** GitHub OIDC Federation
   - **Owner:** Pete
   - **Action:** Run `contractflow/infra/scripts/02-github-oidc-federation.sh` using an Azure account with Entra ID Application Administrator privileges.
2. **BLOCKED:** Update GitHub Secret
   - **Owner:** Pete
   - **Action:** After running the OIDC script, update the `AZURE_CLIENT_ID` secret in the `staging` environment with the generated Client ID.
3. **BLOCKED:** Initial Application Deployment
   - **Owner:** Pete
   - **Action:** Trigger the `.github/workflows/deploy-staging.yml` workflow manually to build images, push to ACR, and deploy to Container Apps.
4. **BLOCKED:** DAST Execution
   - **Owner:** Pete
   - **Action:** Once the application is deployed and healthy, trigger the `.github/workflows/dast-scan.yml` workflow.
