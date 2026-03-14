# Screenshot Evidence Notes

## 2026-03-14 — Azure Portal Login + Cloud Shell
- **File:** `2026-03-14-azure-portal-logged-in.webp`
- **Caption:** Azure Portal home page, logged in as petershamoon97@gmail.com, Cloud Shell (Bash) open at bottom. $185.86 credits remaining, expires March 20, 2026.
- **Significance:** Confirms Azure access and Cloud Shell readiness for ContractFlow staging provisioning.
- **Existing resources visible:** aiuc1-soc2-tools, rg-production, prod-open-nsg, aiuc1stdxbsf, aiuc1-hub-eastus2 (from prior AIUC-1 project)

## 2026-03-14 — Azure CLI Device Code Login Success
- **File:** `login_microsoftonlin_2026-03-14_18-55-20.webp`
- **Caption:** Successful Azure CLI device code authentication. "You have signed in to the Microsoft Azure Cross-platform Command Line Interface application on your device."
- **Significance:** Proves sandbox CLI authenticated to Pete's Azure tenant using secure device code flow — no secrets stored in plaintext. This enables all subsequent provisioning commands.

## 2026-03-14 — Entra App Registrations (All 3 Apps)
- **File:** `2026-03-14-entra-app-registrations-all.webp`
- **Caption:** All 3 Entra app registrations visible: ContractFlow GitHub Deploy, ContractFlow Staging, manus-aiuc1-lab
- **Significance:** Proves all app registrations were created successfully in the tenant

## 2026-03-14 — ContractFlow Staging App Overview
- **File:** `2026-03-14-entra-contractflow-staging-overview.webp`
- **Caption:** ContractFlow Staging app overview showing client ID `41c4eaf5-...`, object ID, identifier URI, 1 SPA redirect, 1 secret
- **Significance:** Proves the main app is correctly configured with all essential properties

## 2026-03-14 — App Roles Configured (5 Roles)
- **File:** `2026-03-14-entra-app-roles-configured.webp`
- **Caption:** 5 app roles configured: SuperAdmin, Admin, Approver, Contributor, Viewer — all Enabled for Users/Groups
- **Significance:** Proves RBAC roles match the identity-and-access-matrix contract

## 2026-03-14 — Exposed API Scope (access_as_user)
- **File:** `2026-03-14-entra-expose-api-scope.webp`
- **Caption:** Exposed API with Application ID URI `api://41c4eaf5-...` and scope `access_as_user` for Admins and users
- **Significance:** Proves the API audience and delegated scope are configured for token validation

## 2026-03-14 — GitHub OIDC Federated Credentials (3 Credentials)
- **File:** `2026-03-14-github-oidc-federated-credentials.webp`
- **Caption:** 3 federated credentials: staging env, production env, main branch — all pointing to `petershamoon/aiuc1-soc2-compliance-lab`
- **Significance:** Proves GitHub OIDC federation is configured for passwordless CI/CD deploys
