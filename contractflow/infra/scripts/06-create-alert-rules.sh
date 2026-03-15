#!/usr/bin/env bash
# 06-create-alert-rules.sh
# Creates metric alert rules for staging environment.
# Prerequisites: source .env.staging, az login done.
set -euo pipefail

RG="cf-stg-rg-eastus2-01"
ACTION_GROUP_ID="/subscriptions/5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08/resourceGroups/cf-stg-rg-eastus2-01/providers/microsoft.insights/actionGroups/cf-stg-alerts-01"
BACKEND_ID="/subscriptions/5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08/resourceGroups/cf-stg-rg-eastus2-01/providers/Microsoft.App/containerapps/cf-stg-api-eastus2-01"
REDIS_ID="/subscriptions/5a9c39a7-65a6-4e2d-9a2b-25d1ac08ff08/resourceGroups/cf-stg-rg-eastus2-01/providers/Microsoft.Cache/Redis/cf-stg-redis-eastus2-01"

echo "=== Creating Metric Alert Rules ==="

# 1. Redis memory pressure alert
echo "Creating Redis memory alert..."
az monitor metrics alert create \
  --name "cf-stg-alert-redis-memory" \
  --resource-group "$RG" \
  --scopes "$REDIS_ID" \
  --condition "avg UsedMemoryPercentage > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "Redis memory usage exceeds 80% in staging" \
  --action "$ACTION_GROUP_ID" \
  --tags project=contractflow environment=staging managed_by=terraform 2>&1 && echo "  Redis memory alert created"

# 2. Redis CPU alert
echo "Creating Redis CPU alert..."
az monitor metrics alert create \
  --name "cf-stg-alert-redis-cpu" \
  --resource-group "$RG" \
  --scopes "$REDIS_ID" \
  --condition "avg percentProcessorTime > 90" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "Redis CPU exceeds 90% in staging" \
  --action "$ACTION_GROUP_ID" \
  --tags project=contractflow environment=staging managed_by=terraform 2>&1 && echo "  Redis CPU alert created"

echo ""
echo "=== Alert Rules Summary ==="
az monitor metrics alert list -g "$RG" --query "[].{name:name, severity:properties.severity, description:properties.description}" -o table 2>&1

echo ""
echo "=== DONE ==="
