#!/usr/bin/env bash
# 03-github-environment-secrets.sh
# Populates GitHub environment secrets for staging deploy workflows.
# Prerequisites: source .env.staging, gh auth login done.
# Updated 2026-03-14: repo changed from aiuc1-soc2-compliance-lab to pipeline-zero
set -euo pipefail

REPO="petershamoon/pipeline-zero"

echo "=== Step 1: Create GitHub Environments ==="
gh api "repos/$REPO/environments/staging" -X PUT --silent
echo "Created/verified staging environment"

gh api "repos/$REPO/environments/production" -X PUT \
  --input - --silent <<'EOF'
{
  "reviewers": [],
  "deployment_branch_policy": {
    "protected_branches": true,
    "custom_branch_policies": false
  }
}
EOF
echo "Created/verified production environment (protected branches only)"

echo ""
echo "=== Step 2: Set Staging Secrets ==="

# Validate required env vars
for var in DEPLOY_APP_CLIENT_ID; do
  if [ -z "${!var:-}" ]; then
    echo "ERROR: $var is not set. Source .env.staging first."
    exit 1
  fi
done

gh secret set AZURE_CLIENT_ID       --repo "$REPO" --env staging --body "${DEPLOY_APP_CLIENT_ID}"
gh secret set AZURE_TENANT_ID       --repo "$REPO" --env staging --body "5d30251d-6d7e-4c8f-849f-90a5c29b3b16"
gh secret set AZURE_SUBSCRIPTION_ID --repo "$REPO" --env staging --body "5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08"
gh secret set ACR_NAME              --repo "$REPO" --env staging --body "cfstg01acr"
gh secret set RESOURCE_GROUP        --repo "$REPO" --env staging --body "cf-stg-rg-eastus2-01"
gh secret set STAGING_BACKEND_APP   --repo "$REPO" --env staging --body "cf-stg-api-eastus2-01"
gh secret set STAGING_FRONTEND_APP  --repo "$REPO" --env staging --body "cf-stg-web-eastus2-01"

echo "Set 7 staging environment secrets"

echo ""
echo "=== Step 3: Verify ==="
gh secret list --repo "$REPO" --env staging

echo ""
echo "════════════════════════════════════════════"
echo "  GITHUB SECRETS POPULATED"
echo "════════════════════════════════════════════"
echo "  Repo: $REPO"
echo "  Note: STAGING_BASE_URL will be set after first deploy"
echo "  (requires frontend FQDN from Container Apps)"
echo "════════════════════════════════════════════"
