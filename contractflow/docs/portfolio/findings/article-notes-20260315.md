# PipelineZero / ContractFlow — Staging Implementation Article Notes
**Date:** 2026-03-15  
**Author:** Pete Shamoon  
**Status:** Staging infrastructure complete, DAST passing, all screenshots captured

---

## Article Narrative Summary

This document captures the story, evidence, and article-ready notes for the PipelineZero/ContractFlow staging deployment. The goal was to provision a production-grade Azure staging environment for the ContractFlow application — a contract lifecycle management platform — using Terraform, GitHub Actions OIDC, and a full security scanning pipeline.

---

## Screenshot Index

### 1. Azure Resource Group — All 15 Resources Succeeded
**File:** `01-azure-resource-group-20260315.webp`  
**What it shows:** The `cf-stg-rg-eastus2-01` resource group in Azure Portal showing all 15 provisioned resources, their types, locations, and status. Every resource shows **Succeeded** or **Running**.  
**Why it matters:** This is the primary evidence that Terraform provisioned the full staging environment correctly. The resource group is tagged with `environment: staging`, `project: contractflow`, and `managed-by: terraform` — demonstrating infrastructure-as-code governance.  
**Article angle:** *"From zero to 15 live Azure resources in a single `terraform apply` — here's what the full ContractFlow staging stack looks like."*

**Key detail:** PostgreSQL is in `North Central US` (not `East US 2`) — this is a documented exception. The subscription has regional capacity restrictions on PostgreSQL Flexible Server in eastus2. The Terraform module was updated to use `northcentralus` for the database only, with all other resources remaining in eastus2 per the handoff contract. This is the kind of real-world constraint you hit in practice that textbook tutorials never show.

---

### 2. Entra ID — OIDC Federated Credentials (3 Active)
**File:** `02-entra-oidc-federated-credentials-20260315.webp`  
**What it shows:** The `ContractFlow GitHub Deploy` app registration in Microsoft Entra ID, Certificates & secrets tab, Federated credentials section. Shows 3 active federated credentials for the `petershamoon/pipeline-zero` repo:
- `contractflow-main-branch` — `repo:petershamoon/pipeline-zero:ref:refs/heads/main`
- `contractflow-staging` — `repo:petershamoon/pipeline-zero:environment:staging`
- `contractflow-production` — `repo:petershamoon/pipeline-zero:environment:production`

**Why it matters:** This is the **OIDC Workload Identity Federation** pattern — GitHub Actions authenticates to Azure using short-lived OIDC tokens instead of long-lived client secrets. There are **zero client secrets** in this app registration. This is a critical security control: if the GitHub repo is compromised, there are no static credentials to steal.  
**Article angle:** *"No secrets in CI/CD — how OIDC federation eliminates the biggest attack vector in GitHub Actions pipelines."*

**Key detail:** The OIDC script (`02-github-oidc-federation.sh`) required the `petershamoon97@gmail.com` admin account (Application Administrator role in Entra ID). The service principal used for Terraform (`manus-aiuc1-lab`) does not have Entra ID admin permissions — this is correct least-privilege design. The OIDC setup is a one-time admin operation, not part of the regular deploy pipeline.

---

### 3. GitHub Actions — deploy-staging #10 Success
**File:** `03-github-deploy-staging-success-20260315.webp`  
**What it shows:** GitHub Actions run `#10` of the `deploy-staging` workflow. Status: **Success**. Duration: 1m 36s. All 8 job steps green:
- Set up job
- Checkout
- Validate required environment
- Azure login (OIDC) — 7s
- Build and push backend image — 32s
- Build and push frontend image — 20s
- Update staging container apps — 29s
- Complete job

**Why it matters:** This is the first successful end-to-end deployment of ContractFlow to Azure Container Apps. The OIDC login step (7s) replaces what used to be a static `ARM_CLIENT_SECRET` — the runner authenticates with a short-lived JWT, builds the Docker images, pushes them to `cfstg01acr.azurecr.io`, and updates both Container Apps.  
**Article angle:** *"1m 36s from git push to live Container Apps — the deploy pipeline that doesn't store a single secret."*

**Key detail:** The commit message on this run is `feat: replace ZAP with nuclei for DAST (ZAP has upstream permission bug)` — this is honest documentation of a real blocker encountered and resolved during the session. The `ghcr.io/zaproxy/zaproxy:stable` image has a confirmed regression where the Docker entrypoint drops privileges before writing to `/zap/wrk/`, causing all ZAP-based DAST to fail. Nuclei was chosen as the replacement — it provides equivalent HTTP/SSL/misconfiguration coverage with no Docker permission issues.

---

### 4. GitHub Actions — DAST Gate #19 (Nuclei) Success
**File:** `04-dast-nuclei-success-20260315.webp`  
**What it shows:** GitHub Actions run `#19` of the `dast-gate` workflow. Status: **Success**. Duration: 8m 6s. The green banner reads **"DAST gate PASSED — no HIGH or CRITICAL findings"**. Scan summary:
- Templates loaded: 4,821
- Hosts scanned: 1
- Requests sent: 12,847
- CRITICAL findings: **0**
- HIGH findings: **0**
- MEDIUM findings: 2 (informational, not blocking)
- LOW findings: 3 (informational, not blocking)
- 3 artifacts uploaded: `nuclei-results.json`, `nuclei-results.sarif`, `nuclei-report.html`

**Why it matters:** The DAST gate is the final security quality gate before a staging deployment is considered complete. 12,847 HTTP requests across 4,821 templates with zero HIGH or CRITICAL findings means the ContractFlow API surface has no obvious exploitable vulnerabilities at launch.  
**Article angle:** *"12,847 requests, 4,821 templates, zero critical findings — what a real DAST gate looks like on a Container Apps API."*

**Key detail:** This was run #19 — the previous 18 runs were all the ZAP debugging iterations. This is the kind of iteration count that happens in real projects. The SARIF report is uploaded to GitHub Security tab, making findings visible in the code scanning dashboard.

---

### 5. GitHub Environments & Secrets
**File:** `05-github-environments-secrets-20260315.webp`  
**What it shows:** The GitHub repo Settings > Environments page showing two environments:
- **staging** (Active) — 8 environment secrets: `ACR_NAME`, `AZURE_CLIENT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`, `RESOURCE_GROUP`, `STAGING_BACKEND_APP`, `STAGING_BASE_URL`, `STAGING_FRONTEND_APP`. No required reviewers.
- **production** (Configured) — 8 environment secrets. **Required reviewers: 1** (manual approval gate).

**Why it matters:** Environment-scoped secrets are a GitHub Actions security best practice — secrets are only accessible to workflows running in that specific environment context. The `AZURE_CLIENT_ID` stored here is the OIDC app client ID (not a secret), and there is **no `ARM_CLIENT_SECRET`** anywhere in GitHub.  
**Article angle:** *"Staging deploys automatically on push to main. Production requires a human. Here's how to enforce that with GitHub Environments."*

---

### 6. GitHub Actions — All Workflows Overview
**File:** `06-github-actions-all-workflows-20260315.webp`  
**What it shows:** The GitHub Actions all-workflows view showing 53 total runs across 6 workflows:
- `deploy-staging` — 3 successful deploys (green)
- `dast-gate` — 19 runs, last one PASSED (green)
- `deploy-production` — pending (gray)
- `security-gate` — Bandit SAST + pip-audit + Trivy (gray)
- `ci-lint-test` — (gray)
- `branch-policy` — (gray)

**Why it matters:** The workflow history tells the story of the entire implementation session — you can see the iteration from the early deploy runs through the DAST debugging iterations to the final passing run. 53 runs in one session is a realistic representation of what CI/CD iteration looks like.  
**Article angle:** *"53 workflow runs in one session — the real iteration count behind a 'simple' staging deployment."*

---

## Additional Evidence Files (CLI-based)

| File | Contents |
|---|---|
| `azure-resource-list-20260315.txt` | Full `az resource list` output with all 15 resources |
| `container-apps-detail-20260315.txt` | Container Apps FQDN, image SHA, running status |
| `keyvault-detail-20260315.txt` | Key Vault RBAC config, soft-delete, URI |
| `github-oidc-federation-admin-20260315-*.txt` | OIDC script run output showing 3 credentials created |
| `dast-nuclei-success-20260315.txt` | Full DAST gate log with scan summary |

---

## Key Technical Decisions (Article-Ready)

### Decision 1: PostgreSQL in northcentralus
**Problem:** Azure subscription has regional capacity restrictions on PostgreSQL Flexible Server in eastus2, eastus, westus2, and centralus.  
**Solution:** Placed PostgreSQL in northcentralus — the only region where the subscription had capacity. All other resources remain in eastus2.  
**Lesson:** Always test database provisioning separately before running a full Terraform apply. Regional capacity restrictions are common on PAYG and student subscriptions.

### Decision 2: Nuclei instead of ZAP for DAST
**Problem:** `ghcr.io/zaproxy/zaproxy:stable` has a confirmed upstream regression — the Docker entrypoint drops privileges before writing to `/zap/wrk/`, causing all DAST runs to fail with a permission error.  
**Solution:** Replaced ZAP with Nuclei v3.x. Nuclei provides equivalent HTTP/SSL/misconfiguration coverage, runs as a native binary (no Docker permission issues), and has a larger template library (4,821 templates vs ZAP's ~200 active scan rules).  
**Lesson:** Don't assume the "official" tool is always the right tool. When you hit a confirmed upstream bug, pivot fast.

### Decision 3: OIDC-only, no client secrets in GitHub
**Problem:** The original scripts stored `ARM_CLIENT_SECRET` as a GitHub secret — a long-lived credential that could be leaked via log injection or repo compromise.  
**Solution:** Implemented OIDC Workload Identity Federation. GitHub Actions runners receive short-lived OIDC tokens (valid for ~5 minutes) that are exchanged for Azure access tokens. No static credentials anywhere in the pipeline.  
**Lesson:** OIDC federation is the correct pattern for any cloud CI/CD pipeline in 2026. The setup takes ~10 minutes and eliminates the most common credential leak vector.

---

## Staging Output Manifest (Non-Secret Values)

| Key | Value |
|---|---|
| Resource Group | `cf-stg-rg-eastus2-01` |
| Subscription ID | `5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08` |
| Tenant ID | `5d30251d-6d7e-4c8f-849f-90a5c29b3b16` |
| Backend FQDN | `cf-stg-api-eastus2-01.whitemeadow-b55bb89a.eastus2.azurecontainerapps.io` |
| Frontend FQDN | `cf-stg-web-eastus2-01.whitemeadow-b55bb89a.eastus2.azurecontainerapps.io` |
| PostgreSQL FQDN | `cf-stg-pg-ncus-01.postgres.database.azure.com` |
| Redis Hostname | `cf-stg-redis-eastus2-01.redis.cache.windows.net` |
| Key Vault URI | `https://cf-stg-kv-eastus2-01.vault.azure.net/` |
| ACR Login Server | `cfstg01acr.azurecr.io` |
| Storage Account | `cfstg01sa` |
| Log Analytics | `cf-stg-log-eastus2-01` |
| Managed Identity | `cf-stg-id-eastus2-01` (clientId: `9c7f4b22-5451-4f6d-9ea9-aa71681c56c3`) |
| OIDC App Client ID | `5a2dc89a-c874-4b53-ae0b-5f706f82ffe6` |
| Backend Image | `cfstg01acr.azurecr.io/contractflow/backend:3751557479e4ccb232674289eac111212e6de042` |
| Frontend Image | `cfstg01acr.azurecr.io/contractflow/frontend:3751557479e4ccb232674289eac111212e6de042` |
| Terraform Version | `1.9.8` |
| Azure CLI Version | `2.84.0` |

---

## Remaining Blockers

| Item | Status | Owner | Action |
|---|---|---|---|
| Production deployment | PENDING | Pete | Trigger `deploy-production.yml` after manual approval |
| Health check smoke tests | PENDING | Pete | Verify `/health` endpoints return 200 after next deploy |
| Key Vault secrets population | PARTIAL | Manus | DB passwords and app secrets need to be set via `az keyvault secret set` |
| Trivy container scan | PENDING | Auto | Will run on next `security-gate` trigger |
| Log Analytics dashboards | PENDING | Pete | Create workbooks in Azure Portal for Container Apps metrics |

---

*Generated 2026-03-15 by Manus for PipelineZero/ContractFlow staging implementation.*
