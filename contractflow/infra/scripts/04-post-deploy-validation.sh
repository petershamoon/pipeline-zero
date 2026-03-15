#!/usr/bin/env bash
# 04-post-deploy-validation.sh
# Validates staging deployment and captures evidence.
# Prerequisites: Terraform applied, container apps deployed.
set -euo pipefail

RG="cf-stg-rg-eastus2-01"
EVIDENCE_DIR="$(cd "$(dirname "$0")/../.." && pwd)/docs/portfolio/findings"
SCREENSHOTS_DIR="$EVIDENCE_DIR/screenshots"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

mkdir -p "$SCREENSHOTS_DIR"

echo "=== Step 1: Get FQDNs ==="
BACKEND_FQDN=$(az containerapp show -n cf-stg-api-eastus2-01 -g "$RG" --query "properties.configuration.ingress.fqdn" -o tsv)
FRONTEND_FQDN=$(az containerapp show -n cf-stg-web-eastus2-01 -g "$RG" --query "properties.configuration.ingress.fqdn" -o tsv)
echo "Backend:  https://$BACKEND_FQDN"
echo "Frontend: https://$FRONTEND_FQDN"

echo ""
echo "=== Step 2: Health Checks ==="
echo "--- Backend /health/live ---"
curl -sf "https://$BACKEND_FQDN/health/live" | python3 -m json.tool || echo "FAILED: backend liveness"

echo ""
echo "--- Backend /health/ready ---"
curl -sf "https://$BACKEND_FQDN/health/ready" | python3 -m json.tool || echo "FAILED: backend readiness"

echo ""
echo "--- Frontend /health ---"
curl -sf "https://$FRONTEND_FQDN/health" | python3 -m json.tool || echo "FAILED: frontend health"

echo ""
echo "=== Step 3: Resource Inventory ==="
az resource list -g "$RG" -o table | tee "$SCREENSHOTS_DIR/${TIMESTAMP}-resource-list.txt"

echo ""
echo "=== Step 4: Container App Status ==="
az containerapp show -n cf-stg-api-eastus2-01 -g "$RG" --query "{name:name, provisioningState:properties.provisioningState, runningStatus:properties.runningStatus, fqdn:properties.configuration.ingress.fqdn}" -o table
az containerapp show -n cf-stg-web-eastus2-01 -g "$RG" --query "{name:name, provisioningState:properties.provisioningState, runningStatus:properties.runningStatus, fqdn:properties.configuration.ingress.fqdn}" -o table

echo ""
echo "=== Step 5: Job Status ==="
az containerapp job show -n cf-stg-job-exp-eastus2-01 -g "$RG" --query "{name:name, provisioningState:properties.provisioningState}" -o table 2>/dev/null || echo "Expiration job not found"
az containerapp job show -n cf-stg-job-notify-eastus2-01 -g "$RG" --query "{name:name, provisioningState:properties.provisioningState}" -o table 2>/dev/null || echo "Notification job not found"

echo ""
echo "=== Step 6: Key Vault Secrets ==="
az keyvault secret list --vault-name cf-stg-kv-eastus2-01 --query "[].{name:name, enabled:attributes.enabled}" -o table

echo ""
echo "=== Step 7: Managed Identity Role Assignments ==="
BACKEND_MI_ID=$(az containerapp show -n cf-stg-api-eastus2-01 -g "$RG" --query "identity.userAssignedIdentities.*.principalId | [0]" -o tsv 2>/dev/null || true)
if [ -n "$BACKEND_MI_ID" ]; then
  az role assignment list --assignee "$BACKEND_MI_ID" --query "[].{role:roleDefinitionName, scope:scope}" -o table
else
  echo "No managed identity found on backend app"
fi

echo ""
echo "=== Step 8: Alert Rules ==="
az monitor metrics alert list -g "$RG" --query "[].{name:name, severity:severity, enabled:enabled}" -o table 2>/dev/null || echo "No metric alerts found"

echo ""
echo "=== Step 9: Set STAGING_BASE_URL ==="
# Updated 2026-03-14: repo changed from aiuc1-soc2-compliance-lab to pipeline-zero
REPO="petershamoon/pipeline-zero"
echo "Setting STAGING_BASE_URL to https://$FRONTEND_FQDN"
gh secret set STAGING_BASE_URL --repo "$REPO" --env staging --body "https://$FRONTEND_FQDN" 2>/dev/null || echo "WARNING: Could not set STAGING_BASE_URL (gh auth may be needed)"

echo ""
echo "=== Step 10: Update Entra Redirect URI ==="
if [ -n "${ENTRA_APP_OBJECT_ID:-}" ]; then
  echo "Adding staging redirect URI to Entra app..."
  az rest --method PATCH \
    --uri "https://graph.microsoft.com/v1.0/applications/$ENTRA_APP_OBJECT_ID" \
    --headers "Content-Type=application/json" \
    --body "{
      \"spa\": {
        \"redirectUris\": [
          \"http://localhost:3000/auth/callback\",
          \"https://$FRONTEND_FQDN/auth/callback\"
        ]
      }
    }" 2>/dev/null || echo "WARNING: Could not update redirect URI"
else
  echo "ENTRA_APP_OBJECT_ID not set, skipping redirect URI update"
fi

echo ""
echo "════════════════════════════════════════════"
echo "  STAGING VALIDATION COMPLETE"
echo "════════════════════════════════════════════"
echo "  Backend:  https://$BACKEND_FQDN"
echo "  Frontend: https://$FRONTEND_FQDN"
echo "  Evidence: $SCREENSHOTS_DIR/${TIMESTAMP}-resource-list.txt"
echo "════════════════════════════════════════════"
