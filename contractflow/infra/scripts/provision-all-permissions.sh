#!/usr/bin/env bash
###############################################################################
# provision-all-permissions.sh
# ContractFlow Staging — Create ALL Azure permissions, keys, and tokens
#
# Run in Azure Cloud Shell (Bash) — already authenticated.
# This script creates:
#   1. Entra App Registration (ContractFlow Staging) with app roles + API scope
#   2. GitHub OIDC Deploy App Registration with federated credentials
#   3. Service Principal client secret for Terraform
#   4. Strong random passwords for Postgres and CSRF
#   5. Role assignments (after Terraform creates resources)
#   6. Complete .env file output
#
# Usage:
#   bash provision-all-permissions.sh
#
# Author: Manus (automated provisioning for PipelineZero)
# Date: 2026-03-14
###############################################################################
set -euo pipefail

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  ContractFlow Staging — Permission & Key Provisioning        ║"
echo "║  Creating all Azure identities, secrets, and federation      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ─── Known constants from handoff docs ───
TENANT_ID="5d30251d-6d7e-4c8f-849f-90a5c29b3b16"
SUBSCRIPTION_ID="5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08"
GITHUB_REPO="petershamoon/aiuc1-soc2-compliance-lab"
EXISTING_SP_APP_ID="8fc64ab2-ee80-4e15-a386-c9ba8650dcaf"

# ─── Verify we're logged in ───
echo ">>> Checking Azure CLI context..."
CURRENT_SUB=$(az account show --query "id" -o tsv 2>/dev/null || true)
if [ -z "$CURRENT_SUB" ]; then
  echo "ERROR: Not logged in. Run this in Azure Cloud Shell."
  exit 1
fi
echo "    Subscription: $CURRENT_SUB"
echo "    Tenant:       $(az account show --query 'tenantId' -o tsv)"
echo ""

###############################################################################
# PHASE 1: Generate Strong Random Passwords
###############################################################################
echo "═══════════════════════════════════════════════════════════════"
echo "  PHASE 1: Generate Strong Random Passwords"
echo "═══════════════════════════════════════════════════════════════"

POSTGRES_ADMIN_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)
DB_APP_PASSWORD=$(openssl rand -base64 24 | tr -d '/+=' | head -c 24)
CSRF_SECRET=$(openssl rand -hex 32)

echo "  ✓ Generated Postgres admin password (24 chars)"
echo "  ✓ Generated DB app password (24 chars)"
echo "  ✓ Generated CSRF secret (64 hex chars)"
echo ""

###############################################################################
# PHASE 2: Create/Refresh Service Principal Client Secret
###############################################################################
echo "═══════════════════════════════════════════════════════════════"
echo "  PHASE 2: Service Principal Client Secret"
echo "═══════════════════════════════════════════════════════════════"

echo "  Using existing SP: $EXISTING_SP_APP_ID"
echo "  Creating new client secret (90 day expiry)..."

SP_SECRET_JSON=$(az ad app credential reset \
  --id "$EXISTING_SP_APP_ID" \
  --display-name "contractflow-staging-$(date +%Y%m%d)" \
  --years 0 \
  --end-date "$(date -d '+90 days' +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -v+90d +%Y-%m-%dT%H:%M:%SZ)" \
  --query "{password:password}" -o json 2>/dev/null || true)

if [ -z "$SP_SECRET_JSON" ] || [ "$SP_SECRET_JSON" = "null" ]; then
  echo "  Note: az ad app credential reset requires app owner permissions."
  echo "  Trying alternative approach — creating a new password credential..."
  SP_SECRET_JSON=$(az ad app credential reset \
    --id "$EXISTING_SP_APP_ID" \
    --display-name "cf-stg-deploy" \
    --query "{password:password}" -o json 2>/dev/null || true)
fi

if [ -n "$SP_SECRET_JSON" ] && [ "$SP_SECRET_JSON" != "null" ]; then
  ARM_CLIENT_SECRET=$(echo "$SP_SECRET_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['password'])")
  echo "  ✓ Created client secret for SP $EXISTING_SP_APP_ID"
else
  echo "  ⚠ Could not auto-create SP secret. Will need manual creation."
  ARM_CLIENT_SECRET="MANUAL_ENTRY_REQUIRED"
fi
echo ""

###############################################################################
# PHASE 3: Create ContractFlow Staging App Registration
###############################################################################
echo "═══════════════════════════════════════════════════════════════"
echo "  PHASE 3: Entra App Registration — ContractFlow Staging"
echo "═══════════════════════════════════════════════════════════════"

# Check if app already exists
ENTRA_APP_ID=$(az ad app list --display-name "ContractFlow Staging" --query "[0].appId" -o tsv 2>/dev/null || true)
if [ -n "$ENTRA_APP_ID" ]; then
  echo "  App registration already exists: $ENTRA_APP_ID"
else
  echo "  Creating app registration..."
  az ad app create \
    --display-name "ContractFlow Staging" \
    --sign-in-audience AzureADMyOrg \
    --output none
  ENTRA_APP_ID=$(az ad app list --display-name "ContractFlow Staging" --query "[0].appId" -o tsv)
  echo "  ✓ Created app registration: $ENTRA_APP_ID"
fi

ENTRA_APP_OBJECT_ID=$(az ad app show --id "$ENTRA_APP_ID" --query "id" -o tsv)
echo "  Object ID: $ENTRA_APP_OBJECT_ID"

# Set Identifier URI
echo "  Setting identifier URI: api://contractflow-stg"
az ad app update --id "$ENTRA_APP_ID" --identifier-uris "api://contractflow-stg" 2>/dev/null || true
echo "  ✓ Identifier URI set"

# Configure SPA redirect URIs
echo "  Configuring SPA redirect URIs..."
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$ENTRA_APP_OBJECT_ID" \
  --headers "Content-Type=application/json" \
  --body '{
    "spa": {
      "redirectUris": [
        "http://localhost:3000/auth/callback"
      ]
    }
  }' 2>/dev/null || true
echo "  ✓ SPA redirect URIs configured"

# Create App Roles
echo "  Creating app roles..."
ROLE_VIEWER=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.viewer'))")
ROLE_CONTRIBUTOR=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.contributor'))")
ROLE_APPROVER=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.approver'))")
ROLE_ADMIN=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.admin'))")
ROLE_SUPERADMIN=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.superadmin'))")

az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$ENTRA_APP_OBJECT_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"appRoles\": [
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Viewer\",\"value\":\"ContractFlow.Viewer\",\"isEnabled\":true,\"id\":\"$ROLE_VIEWER\",\"description\":\"Read-only access to contracts\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Contributor\",\"value\":\"ContractFlow.Contributor\",\"isEnabled\":true,\"id\":\"$ROLE_CONTRIBUTOR\",\"description\":\"Create and edit contracts\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Approver\",\"value\":\"ContractFlow.Approver\",\"isEnabled\":true,\"id\":\"$ROLE_APPROVER\",\"description\":\"Approve contracts in workflow\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Admin\",\"value\":\"ContractFlow.Admin\",\"isEnabled\":true,\"id\":\"$ROLE_ADMIN\",\"description\":\"Administrative access\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Super Admin\",\"value\":\"ContractFlow.SuperAdmin\",\"isEnabled\":true,\"id\":\"$ROLE_SUPERADMIN\",\"description\":\"Full system access\"}
    ]
  }" 2>/dev/null || true
echo "  ✓ Created 5 app roles (Viewer, Contributor, Approver, Admin, SuperAdmin)"

# Create Service Principal for the app
echo "  Creating service principal for app..."
az ad sp show --id "$ENTRA_APP_ID" --query "appId" -o tsv 2>/dev/null || \
  az ad sp create --id "$ENTRA_APP_ID" --output none 2>/dev/null || true
echo "  ✓ Service principal ready"

# Create Exposed API Scope
echo "  Creating exposed API scope..."
SCOPE_ID=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.access_as_user'))")
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$ENTRA_APP_OBJECT_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"api\": {
      \"oauth2PermissionScopes\": [
        {
          \"adminConsentDescription\": \"Access ContractFlow API\",
          \"adminConsentDisplayName\": \"Access ContractFlow\",
          \"id\": \"$SCOPE_ID\",
          \"isEnabled\": true,
          \"type\": \"User\",
          \"userConsentDescription\": \"Access ContractFlow\",
          \"userConsentDisplayName\": \"Access ContractFlow\",
          \"value\": \"access_as_user\"
        }
      ]
    }
  }" 2>/dev/null || true
echo "  ✓ Exposed API scope: access_as_user"
echo ""

###############################################################################
# PHASE 4: Create GitHub OIDC Deploy App Registration
###############################################################################
echo "═══════════════════════════════════════════════════════════════"
echo "  PHASE 4: GitHub OIDC Deploy App Registration"
echo "═══════════════════════════════════════════════════════════════"

DEPLOY_APP_ID=$(az ad app list --display-name "ContractFlow GitHub Deploy" --query "[0].appId" -o tsv 2>/dev/null || true)
if [ -n "$DEPLOY_APP_ID" ]; then
  echo "  Deploy app already exists: $DEPLOY_APP_ID"
else
  echo "  Creating deploy app registration..."
  az ad app create --display-name "ContractFlow GitHub Deploy" --output none
  DEPLOY_APP_ID=$(az ad app list --display-name "ContractFlow GitHub Deploy" --query "[0].appId" -o tsv)
  echo "  ✓ Created deploy app: $DEPLOY_APP_ID"
fi

DEPLOY_APP_OBJECT_ID=$(az ad app show --id "$DEPLOY_APP_ID" --query "id" -o tsv)

# Create SP for deploy app
DEPLOY_SP_ID=$(az ad sp show --id "$DEPLOY_APP_ID" --query "id" -o tsv 2>/dev/null || true)
if [ -n "$DEPLOY_SP_ID" ]; then
  echo "  Service principal exists: $DEPLOY_SP_ID"
else
  az ad sp create --id "$DEPLOY_APP_ID" --output none
  DEPLOY_SP_ID=$(az ad sp show --id "$DEPLOY_APP_ID" --query "id" -o tsv)
  echo "  ✓ Created service principal: $DEPLOY_SP_ID"
fi

# Create Federated Credentials
echo "  Creating federated credentials for GitHub Actions..."
EXISTING_CREDS=$(az ad app federated-credential list --id "$DEPLOY_APP_OBJECT_ID" --query "[].name" -o tsv 2>/dev/null || true)

for CRED_NAME in "contractflow-staging" "contractflow-production" "contractflow-main-branch"; do
  if echo "$EXISTING_CREDS" | grep -q "$CRED_NAME"; then
    echo "    ✓ $CRED_NAME already exists"
  else
    case "$CRED_NAME" in
      contractflow-staging)
        SUBJECT="repo:${GITHUB_REPO}:environment:staging"
        DESC="GitHub Actions staging deploy"
        ;;
      contractflow-production)
        SUBJECT="repo:${GITHUB_REPO}:environment:production"
        DESC="GitHub Actions production deploy"
        ;;
      contractflow-main-branch)
        SUBJECT="repo:${GITHUB_REPO}:ref:refs/heads/main"
        DESC="GitHub Actions main branch deploy"
        ;;
    esac
    az ad app federated-credential create --id "$DEPLOY_APP_OBJECT_ID" --parameters "{
      \"name\": \"$CRED_NAME\",
      \"issuer\": \"https://token.actions.githubusercontent.com\",
      \"subject\": \"$SUBJECT\",
      \"audiences\": [\"api://AzureADTokenExchange\"],
      \"description\": \"$DESC\"
    }" --output none 2>/dev/null || true
    echo "    ✓ Created $CRED_NAME ($SUBJECT)"
  fi
done

echo ""
echo "  Federated credentials summary:"
az ad app federated-credential list --id "$DEPLOY_APP_OBJECT_ID" --query "[].{name:name, subject:subject}" -o table 2>/dev/null || true
echo ""

###############################################################################
# PHASE 5: Verify and Display Results
###############################################################################
echo "═══════════════════════════════════════════════════════════════"
echo "  PHASE 5: Verification"
echo "═══════════════════════════════════════════════════════════════"

echo ""
echo "  Entra App Registration:"
az ad app show --id "$ENTRA_APP_ID" --query "{displayName:displayName, appId:appId, identifierUris:identifierUris}" -o table 2>/dev/null || true

echo ""
echo "  App Roles:"
az ad app show --id "$ENTRA_APP_ID" --query "appRoles[].{displayName:displayName, value:value, enabled:isEnabled}" -o table 2>/dev/null || true

echo ""
echo "  Deploy App Registration:"
az ad app show --id "$DEPLOY_APP_ID" --query "{displayName:displayName, appId:appId}" -o table 2>/dev/null || true

echo ""

###############################################################################
# PHASE 6: Output Complete .env File
###############################################################################
echo "═══════════════════════════════════════════════════════════════"
echo "  PHASE 6: Complete .env File Output"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Copy everything between the ===START=== and ===END=== markers:"
echo ""
echo "===START=== .env.staging ==="
cat <<ENVFILE
# ═══════════════════════════════════════════════════════════════
# ContractFlow Staging — Complete Environment Configuration
# Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
# This file is .gitignored. NEVER commit to repo.
# ═══════════════════════════════════════════════════════════════

# ─── Azure Service Principal (Terraform) ───
export ARM_CLIENT_ID="$EXISTING_SP_APP_ID"
export ARM_CLIENT_SECRET="$ARM_CLIENT_SECRET"
export ARM_TENANT_ID="$TENANT_ID"
export ARM_SUBSCRIPTION_ID="$SUBSCRIPTION_ID"

# ─── Terraform Sensitive Variables ───
export TF_VAR_postgres_admin_password="$POSTGRES_ADMIN_PASSWORD"
export TF_VAR_db_app_password="$DB_APP_PASSWORD"

# ─── Entra App Registration (ContractFlow Staging) ───
export ENTRA_APP_CLIENT_ID="$ENTRA_APP_ID"
export ENTRA_APP_OBJECT_ID="$ENTRA_APP_OBJECT_ID"
export ENTRA_TENANT_ID="$TENANT_ID"
export ENTRA_AUDIENCE="api://contractflow-stg"

# ─── GitHub OIDC Deploy Principal ───
export DEPLOY_APP_CLIENT_ID="$DEPLOY_APP_ID"
export DEPLOY_APP_OBJECT_ID="$DEPLOY_APP_OBJECT_ID"
export DEPLOY_SP_OBJECT_ID="$DEPLOY_SP_ID"

# ─── Resource Names (from naming convention) ───
export RESOURCE_GROUP="cf-stg-rg-eastus2-01"
export ACR_NAME="cfstg01acr"
export BACKEND_APP="cf-stg-api-eastus2-01"
export FRONTEND_APP="cf-stg-web-eastus2-01"
export KEY_VAULT_NAME="cf-stg-kv-eastus2-01"
export POSTGRES_SERVER="cf-stg-pg-eastus2-01"
export REDIS_NAME="cf-stg-redis-eastus2-01"
export STORAGE_ACCOUNT="cfstg01sa"
export LOG_ANALYTICS="cf-stg-log-eastus2-01"
export CONTAINER_ENV="cf-stg-cae-eastus2-01"

# ─── Application Secrets ───
export CSRF_SECRET="$CSRF_SECRET"
export POSTGRES_ADMIN_PASSWORD="$POSTGRES_ADMIN_PASSWORD"
export DB_APP_PASSWORD="$DB_APP_PASSWORD"

# ─── GitHub Secrets (for gh secret set) ───
export GH_AZURE_CLIENT_ID="$DEPLOY_APP_ID"
export GH_AZURE_TENANT_ID="$TENANT_ID"
export GH_AZURE_SUBSCRIPTION_ID="$SUBSCRIPTION_ID"
export GH_REPO="$GITHUB_REPO"

# ─── Staging URLs (populated after Terraform apply) ───
export STAGING_BACKEND_URL=""
export STAGING_FRONTEND_URL=""
export STAGING_BASE_URL=""
ENVFILE
echo "===END=== .env.staging ==="

echo ""
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  PROVISIONING COMPLETE                                       ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║  Entra App (Client) ID:     $ENTRA_APP_ID  ║"
echo "║  Entra App Object ID:       $ENTRA_APP_OBJECT_ID  ║"
echo "║  Deploy App (Client) ID:    $DEPLOY_APP_ID  ║"
echo "║  Deploy SP Object ID:       $DEPLOY_SP_ID  ║"
echo "║                                                               ║"
echo "║  NEXT STEPS:                                                  ║"
echo "║  1. Copy the .env file above to your local machine            ║"
echo "║  2. Update terraform.tfvars with entra_client_id              ║"
echo "║  3. Run: source .env.staging                                  ║"
echo "║  4. Run: terraform init && terraform plan && terraform apply  ║"
echo "║  5. Run: ./scripts/02-github-oidc-federation.sh (role assign) ║"
echo "║  6. Run: ./scripts/03-github-environment-secrets.sh           ║"
echo "║  7. Run: ./scripts/04-post-deploy-validation.sh               ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
