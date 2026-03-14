# Environment Variables And Secrets Matrix

Last updated: 2026-03-08

## Rules
- Production secrets live in Key Vault only.
- Local `.env` is allowed for local development only.
- No secret values in git, CI logs, or workflow YAML.

## Backend runtime variables
| Key | Required | Secret | Environment(s) | Owner | Source of truth | Validation |
|---|---|---|---|---|---|---|
| `ENVIRONMENT` | Yes | No | all | Codex/Claude | `backend/app/core/config.py` | startup + `/health/ready` |
| `DATABASE_URL` | Yes | Yes | all | Manus | Key Vault -> Container App secret ref | migration + DB query smoke |
| `REDIS_URL` | Yes | Yes | all | Manus | Key Vault -> Container App secret ref | `/health/ready` redis ping |
| `ALLOWED_ORIGINS` | Yes | No | all | Codex/Claude | app settings contract | CORS preflight smoke |
| `AZURE_STORAGE_ACCOUNT_URL` | Yes | No | all | Manus | Terraform output / storage endpoint | upload/download smoke |
| `AZURE_STORAGE_CONTAINER` | Yes | No | all | Codex/Claude | app settings | upload smoke |
| `KEY_VAULT_URI` | Yes | No | cloud | Manus | Terraform output | managed identity token + secret read |
| `ENTRA_TENANT_ID` | Yes | No | cloud | Manus | Entra app registration | JWT issuer check |
| `ENTRA_CLIENT_ID` | Yes | No | cloud | Manus | Entra app registration | auth init |
| `ENTRA_AUDIENCE` | Yes | No | cloud | Codex/Claude + Manus | app auth config + Entra exposed API | JWT audience check |
| `CSRF_SECRET` | Yes | Yes | all | Manus | Key Vault | session + CSRF flow test |
| `LOCAL_AUTH_ENABLED` | Yes | No | all | Codex/Claude | app config | production startup must fail if `true` |
| `SESSION_COOKIE_NAME` | Yes | No | all | Codex/Claude | app config | browser auth smoke |
| `CSRF_COOKIE_NAME` | Yes | No | all | Codex/Claude | app config | CSRF header/cookie check |
| `SESSION_TTL_MINUTES` | Yes | No | all | Codex/Claude | app config | session expiry behavior |
| `SESSION_SECURE_COOKIE` | Yes | No | all | Codex/Claude | app config | secure cookie flags in cloud |
| `MAX_UPLOAD_SIZE_MB` | Yes | No | all | Codex/Claude | app config | reject oversize file |
| `SAS_URL_TTL_MINUTES` | Yes | No | all | Codex/Claude | app config | signed URL expiry behavior |

## Frontend runtime variables
| Key | Required | Secret | Environment(s) | Owner | Source of truth | Validation |
|---|---|---|---|---|---|---|
| `VITE_API_URL` | Yes | No | all | Codex/Claude | deploy config | API request smoke |
| `VITE_ENTRA_CLIENT_ID` | Yes | No | cloud | Manus | Entra app registration | login init |
| `VITE_ENTRA_AUTHORITY` | Yes | No | cloud | Manus | Entra tenant endpoint | login init |
| `VITE_ENTRA_REDIRECT_URI` | Yes | No | cloud | Manus | Entra app registration | callback flow |

## GitHub Actions secrets (deploy/security)
| Secret key | Required | Owner | Used by | Validation |
|---|---|---|---|---|
| `AZURE_CLIENT_ID` | Yes | Manus | `deploy-staging.yml`, `deploy-production.yml` | `azure/login` succeeds |
| `AZURE_TENANT_ID` | Yes | Manus | deploy workflows | `azure/login` succeeds |
| `AZURE_SUBSCRIPTION_ID` | Yes | Manus | deploy workflows | `azure/login` succeeds |
| `ACR_NAME` | Yes | Manus | deploy workflows | image push/pull succeeds |
| `RESOURCE_GROUP` | Yes | Manus | deploy workflows | `az containerapp update` succeeds |
| `STAGING_BACKEND_APP` | Yes | Manus | staging deploy workflow | backend app update succeeds |
| `STAGING_FRONTEND_APP` | Yes | Manus | staging deploy workflow | frontend app update succeeds |
| `PRODUCTION_BACKEND_APP` | Yes | Manus | production deploy workflow | backend app update succeeds |
| `PRODUCTION_FRONTEND_APP` | Yes | Manus | production deploy workflow | frontend app update succeeds |
| `STAGING_BASE_URL` | Yes | Manus | `dast.yml` | ZAP baseline completes |

## Secret rotation policy
- Rotation interval: every 90 days minimum for app-managed secrets.
- Emergency rotation SLA: within 4 hours of confirmed compromise.

## Open items
- `BLOCKED` (Owner: Manus, Due: 2026-03-15): set all cloud secret values in staging Key Vault and GitHub environments.
- `BLOCKED` (Owner: Manus, Due: 2026-03-22): mirror validated staging values into production with environment approvals.

## Rollback/fallback notes
- If a rotated secret causes runtime failure, revert the affected Key Vault secret version and redeploy the previous working revision.
- If Entra values are misconfigured in staging, set `LOCAL_AUTH_ENABLED=true` only in local development; do not enable local auth in production.
