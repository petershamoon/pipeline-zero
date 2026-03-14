#!/usr/bin/env bash
# 01-entra-app-registration.sh
# Creates the ContractFlow Staging Entra app registration with app roles.
# Prerequisites: source .env.staging (ARM_* vars set), az login done.
set -euo pipefail

echo "=== Step 1: Create ContractFlow Staging App Registration ==="

# Check if app already exists
EXISTING=$(az ad app list --display-name "ContractFlow Staging" --query "[0].appId" -o tsv 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
  echo "App registration already exists: $EXISTING"
  APP_ID="$EXISTING"
else
  az ad app create \
    --display-name "ContractFlow Staging" \
    --sign-in-audience AzureADMyOrg
  APP_ID=$(az ad app list --display-name "ContractFlow Staging" --query "[0].appId" -o tsv)
  echo "Created app registration: $APP_ID"
fi

APP_OBJECT_ID=$(az ad app show --id "$APP_ID" --query "id" -o tsv)
echo "App Object ID: $APP_OBJECT_ID"

echo ""
echo "=== Step 2: Set Identifier URI ==="
az ad app update --id "$APP_ID" --identifier-uris "api://contractflow-stg"
echo "Set identifier URI: api://contractflow-stg"

echo ""
echo "=== Step 3: Configure SPA Platform Redirect URIs ==="
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" \
  --headers "Content-Type=application/json" \
  --body '{
    "spa": {
      "redirectUris": [
        "http://localhost:3000/auth/callback"
      ]
    }
  }'
echo "Set SPA redirect URIs (localhost for now; staging FQDN added after deploy)"

echo ""
echo "=== Step 4: Create App Roles ==="
# Generate deterministic UUIDs for app roles
ROLE_VIEWER=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.viewer'))")
ROLE_CONTRIBUTOR=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.contributor'))")
ROLE_APPROVER=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.approver'))")
ROLE_ADMIN=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.admin'))")
ROLE_SUPERADMIN=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.superadmin'))")

az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" \
  --headers "Content-Type=application/json" \
  --body "{
    \"appRoles\": [
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Viewer\",\"value\":\"ContractFlow.Viewer\",\"isEnabled\":true,\"id\":\"$ROLE_VIEWER\",\"description\":\"Read-only access to contracts\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Contributor\",\"value\":\"ContractFlow.Contributor\",\"isEnabled\":true,\"id\":\"$ROLE_CONTRIBUTOR\",\"description\":\"Create and edit contracts\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Approver\",\"value\":\"ContractFlow.Approver\",\"isEnabled\":true,\"id\":\"$ROLE_APPROVER\",\"description\":\"Approve contracts in workflow\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Admin\",\"value\":\"ContractFlow.Admin\",\"isEnabled\":true,\"id\":\"$ROLE_ADMIN\",\"description\":\"Administrative access\"},
      {\"allowedMemberTypes\":[\"User\"],\"displayName\":\"ContractFlow Super Admin\",\"value\":\"ContractFlow.SuperAdmin\",\"isEnabled\":true,\"id\":\"$ROLE_SUPERADMIN\",\"description\":\"Full system access\"}
    ]
  }"
echo "Created 5 app roles"

echo ""
echo "=== Step 5: Create Service Principal ==="
SP_EXISTS=$(az ad sp show --id "$APP_ID" --query "appId" -o tsv 2>/dev/null || true)
if [ -n "$SP_EXISTS" ]; then
  echo "Service principal already exists"
else
  az ad sp create --id "$APP_ID"
  echo "Created service principal"
fi

echo ""
echo "=== Step 6: Add Exposed API Scope ==="
SCOPE_ID=$(python3 -c "import uuid; print(uuid.uuid5(uuid.NAMESPACE_DNS, 'contractflow.access_as_user'))")
az rest --method PATCH \
  --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" \
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
  }"
echo "Created exposed API scope: access_as_user"

echo ""
echo "════════════════════════════════════════════"
echo "  ENTRA APP REGISTRATION COMPLETE"
echo "════════════════════════════════════════════"
echo "  App (Client) ID:  $APP_ID"
echo "  Object ID:        $APP_OBJECT_ID"
echo "  Identifier URI:   api://contractflow-stg"
echo "  App Roles:        5 (Viewer, Contributor, Approver, Admin, SuperAdmin)"
echo ""
echo "  → Update .env.staging:"
echo "    ENTRA_APP_CLIENT_ID=$APP_ID"
echo "    ENTRA_APP_OBJECT_ID=$APP_OBJECT_ID"
echo ""
echo "  → Update terraform.tfvars:"
echo "    entra_client_id = \"$APP_ID\""
echo "════════════════════════════════════════════"
