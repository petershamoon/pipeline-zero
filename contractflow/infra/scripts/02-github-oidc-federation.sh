#!/usr/bin/env bash
# 02-github-oidc-federation.sh
# Creates the GitHub OIDC deploy principal with federated credentials.
# Prerequisites: source .env.staging, az login done.
set -euo pipefail

# Updated 2026-03-14: repo changed from aiuc1-soc2-compliance-lab to pipeline-zero
GITHUB_REPO="petershamoon/pipeline-zero"

echo "=== Step 1: Create GitHub Deploy App Registration ==="

EXISTING=$(az ad app list --display-name "ContractFlow GitHub Deploy" --query "[0].appId" -o tsv 2>/dev/null || true)
if [ -n "$EXISTING" ]; then
  echo "Deploy app already exists: $EXISTING"
  DEPLOY_APP_ID="$EXISTING"
else
  az ad app create --display-name "ContractFlow GitHub Deploy"
  DEPLOY_APP_ID=$(az ad app list --display-name "ContractFlow GitHub Deploy" --query "[0].appId" -o tsv)
  echo "Created deploy app: $DEPLOY_APP_ID"
fi

DEPLOY_OBJECT_ID=$(az ad app show --id "$DEPLOY_APP_ID" --query "id" -o tsv)

echo ""
echo "=== Step 2: Create Service Principal ==="
SP_EXISTS=$(az ad sp show --id "$DEPLOY_APP_ID" --query "id" -o tsv 2>/dev/null || true)
if [ -n "$SP_EXISTS" ]; then
  DEPLOY_SP_ID="$SP_EXISTS"
  echo "Service principal already exists: $DEPLOY_SP_ID"
else
  az ad sp create --id "$DEPLOY_APP_ID"
  DEPLOY_SP_ID=$(az ad sp show --id "$DEPLOY_APP_ID" --query "id" -o tsv)
  echo "Created service principal: $DEPLOY_SP_ID"
fi

echo ""
echo "=== Step 3: Create Federated Credentials ==="

# Check if credentials already exist
EXISTING_CREDS=$(az ad app federated-credential list --id "$DEPLOY_OBJECT_ID" --query "[].name" -o tsv 2>/dev/null || true)

if echo "$EXISTING_CREDS" | grep -q "contractflow-staging"; then
  echo "Staging credential already exists, skipping"
else
  az ad app federated-credential create --id "$DEPLOY_OBJECT_ID" --parameters "{
    \"name\": \"contractflow-staging\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${GITHUB_REPO}:environment:staging\",
    \"audiences\": [\"api://AzureADTokenExchange\"],
    \"description\": \"GitHub Actions staging deploy\"
  }"
  echo "Created staging federated credential"
fi

if echo "$EXISTING_CREDS" | grep -q "contractflow-production"; then
  echo "Production credential already exists, skipping"
else
  az ad app federated-credential create --id "$DEPLOY_OBJECT_ID" --parameters "{
    \"name\": \"contractflow-production\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${GITHUB_REPO}:environment:production\",
    \"audiences\": [\"api://AzureADTokenExchange\"],
    \"description\": \"GitHub Actions production deploy\"
  }"
  echo "Created production federated credential"
fi

if echo "$EXISTING_CREDS" | grep -q "contractflow-main-branch"; then
  echo "Main branch credential already exists, skipping"
else
  az ad app federated-credential create --id "$DEPLOY_OBJECT_ID" --parameters "{
    \"name\": \"contractflow-main-branch\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${GITHUB_REPO}:ref:refs/heads/main\",
    \"audiences\": [\"api://AzureADTokenExchange\"],
    \"description\": \"GitHub Actions main branch deploy\"
  }"
  echo "Created main branch federated credential"
fi

echo ""
echo "=== Step 4: Assign Roles ==="

RG_NAME="cf-stg-rg-eastus2-01"
ACR_NAME="cfstg01acr"

# Check if RG exists (it may not yet if Terraform hasn't run)
RG_EXISTS=$(az group show -n "$RG_NAME" --query "id" -o tsv 2>/dev/null || true)
if [ -n "$RG_EXISTS" ]; then
  # Contributor on RG
  EXISTING_ROLE=$(az role assignment list --assignee "$DEPLOY_SP_ID" --scope "$RG_EXISTS" --role "Contributor" --query "[0].id" -o tsv 2>/dev/null || true)
  if [ -z "$EXISTING_ROLE" ]; then
    az role assignment create --assignee "$DEPLOY_SP_ID" --role "Contributor" --scope "$RG_EXISTS"
    echo "Assigned Contributor on RG"
  else
    echo "Contributor role already assigned on RG"
  fi

  # AcrPush on ACR
  ACR_ID=$(az acr show -n "$ACR_NAME" --query "id" -o tsv 2>/dev/null || true)
  if [ -n "$ACR_ID" ]; then
    EXISTING_ACR_ROLE=$(az role assignment list --assignee "$DEPLOY_SP_ID" --scope "$ACR_ID" --role "AcrPush" --query "[0].id" -o tsv 2>/dev/null || true)
    if [ -z "$EXISTING_ACR_ROLE" ]; then
      az role assignment create --assignee "$DEPLOY_SP_ID" --role "AcrPush" --scope "$ACR_ID"
      echo "Assigned AcrPush on ACR"
    else
      echo "AcrPush role already assigned on ACR"
    fi
  else
    echo "WARNING: ACR not found. Run Terraform first, then re-run this script for role assignments."
  fi
else
  echo "WARNING: Resource group not found. Run Terraform first, then re-run this script for role assignments."
fi

echo ""
echo "════════════════════════════════════════════"
echo "  GITHUB OIDC FEDERATION COMPLETE"
echo "════════════════════════════════════════════"
echo "  Deploy App (Client) ID:  $DEPLOY_APP_ID"
echo "  Deploy App Object ID:    $DEPLOY_OBJECT_ID"
echo "  Deploy SP Object ID:     $DEPLOY_SP_ID"
echo ""
echo "  Federated credentials:"
az ad app federated-credential list --id "$DEPLOY_OBJECT_ID" --query "[].{name:name, subject:subject}" -o table
echo ""
echo "  → Update .env.staging:"
echo "    DEPLOY_APP_CLIENT_ID=$DEPLOY_APP_ID"
echo "    DEPLOY_APP_OBJECT_ID=$DEPLOY_OBJECT_ID"
echo "    DEPLOY_SP_OBJECT_ID=$DEPLOY_SP_ID"
echo ""
echo "  → This DEPLOY_APP_CLIENT_ID becomes AZURE_CLIENT_ID in GitHub secrets"
echo "════════════════════════════════════════════"
