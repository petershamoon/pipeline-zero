# Azure Resource Contract

Last updated: 2026-03-08

This document defines the minimum Azure resources required for ContractFlow.
Canonical naming and interface contract is defined in:
- `contractflow/infra/main.tf`
- `contractflow/infra/variables.tf`
- `contractflow/infra/modules/platform/main.tf`

## Required resources
| Resource | Scope | Required | Purpose | Source of truth | Validation |
|---|---|---|---|---|---|
| Resource Group | per env | Yes | Resource boundary and RBAC scope | `module.platform.resource_names.resource_group` | `az group show -n <resource_group>` |
| Container Apps Environment | per env | Yes | Runtime host for apps/jobs | `module.platform.resource_names.container_env` | `az containerapp env show -n <container_env> -g <resource_group>` |
| Container App: backend | per env | Yes | FastAPI runtime | `module.platform.resource_names.backend_container_app` | `az containerapp show ...` + `GET /health/ready` |
| Container App: frontend | per env | Yes | SPA runtime | `module.platform.resource_names.frontend_container_app` | `az containerapp show ...` + `GET /health` |
| Container App Job: expiration | per env | Yes | Scheduled contract expiration processing | `module.platform.resource_names.expiration_job` | `az containerapp job show ...` + execution log |
| Container App Job: notification | per env | Yes | Scheduled contract notification processing | `module.platform.resource_names.notification_job` | `az containerapp job show ...` + execution log |
| PostgreSQL Flexible Server | per env | Yes | Primary relational store | `module.platform.resource_names.postgres_server` | backend migration and query smoke |
| Azure Cache for Redis | per env | Yes | Distributed limiter/session coordination | `module.platform.resource_names.redis_cache` | backend `/health/ready` redis ping path |
| Storage Account + Blob Container | per env | Yes | Contract file storage | `module.platform.resource_names.storage_account` | upload + signed download smoke |
| Key Vault | per env | Yes | Secret management | `module.platform.resource_names.key_vault` | managed identity secret read |
| Azure Container Registry | shared or per env | Yes | Image registry for backend/frontend images | `module.platform.resource_names.acr` | image push/pull in deploy workflows |
| Log Analytics Workspace | per env | Yes | Logs and metrics sink | `module.platform.resource_names.log_analytics_workspace` | logs visible in workspace |
| Azure Monitor Alerts | per env | Yes | Operational alerting | Manus alert config | synthetic alert tests |

## Resource naming rules
- Pattern: `cf-<env>-<service>-<region>-<nn>`
- `env` must be `stg` or `prd`
- Do not reuse production names for staging resources.

## Tagging rules
Required tags on every resource:
- `project=contractflow`
- `environment=staging|production`
- `owner=manus`
- `managed_by=terraform`
- `data_classification=internal`

## Environment examples
- Staging baseline: `contractflow/infra/envs/staging/terraform.tfvars.example`
- Production baseline: `contractflow/infra/envs/production/terraform.tfvars.example`

## Open items
- `BLOCKED` (Owner: Manus, Due: 2026-03-15): final concrete values for each `resource_names.*` output after first staging `terraform apply`.

## Failure fallback
- If private networking blocks initial delivery, temporary public ingress may be used in staging only with IP restrictions and explicit expiration date.
