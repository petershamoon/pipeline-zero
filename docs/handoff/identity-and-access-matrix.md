# Identity And Access Matrix

Last updated: 2026-03-08

## Identity model
- Production identity provider: Microsoft Entra ID.
- Backend accepts Entra bearer tokens and maps role claims to internal roles.
- Local cookie-session auth is development-only fallback and must be disabled in production.

## Principal matrix
| Principal | Type | Scope | Required permissions | Owner | Source of truth | Validation |
|---|---|---|---|---|---|---|
| GitHub OIDC deploy principal | Federated identity | RG/env | push images, update container apps/jobs | Manus | Entra federated credentials + role assignments | staging deploy workflow success |
| Backend managed identity | System/User-assigned MI | app env | Key Vault secret read, Blob read/write, telemetry write | Manus | Container App identity config | backend startup + secret read |
| Job managed identity | System/User-assigned MI | jobs env | DB/Redis access, Key Vault read, telemetry write | Manus | Container App Job identity config | scheduled job run success |
| Frontend deploy principal | Federated identity | RG/env | update frontend container app | Manus | Entra federated credentials + role assignments | frontend deploy success |
| DB app user | Database role | DB | least privilege CRUD for app schema only | Manus | DB provisioning script | migration + app integration tests |

## Entra role/group mapping
| Entra app role/group | Internal role | Implemented in code |
|---|---|---|
| `ContractFlow.Viewer` | `viewer` | `backend/app/services/entra.py` |
| `ContractFlow.Contributor` | `contributor` | `backend/app/services/entra.py` |
| `ContractFlow.Approver` | `approver` | `backend/app/services/entra.py` |
| `ContractFlow.Admin` | `admin` | `backend/app/services/entra.py` |
| `ContractFlow.SuperAdmin` | `super_admin` | `backend/app/services/entra.py` |

## OIDC federation contract
- Deploy workflows use `azure/login@v2` with:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`
- Expected subjects must map to GitHub environment-scoped runs for `staging` and `production`.

## Access control rules
- No contributor role assignment at subscription root scope.
- No ACR admin account usage in runtime.
- All production changes require auditable identity and environment approvals.

## Validation commands
- `az role assignment list --assignee <principalId> --scope <scope>`
- `az ad app federated-credential list --id <appId>`
- Login flow test confirms expected role claims are present.

## Open items
- `BLOCKED` (Owner: Manus, Due: 2026-03-15): create Entra app registrations and publish concrete app IDs for SPA/API.
- `BLOCKED` (Owner: Manus, Due: 2026-03-15): configure federated credential subject patterns using actual repo slug and environment names.

## Rollback/fallback notes
- If OIDC deploy auth fails after credential changes, temporarily disable deployment workflows and restore previous federated credential bindings.
- If Entra role claims mismatch expected app roles, roll back app role assignment changes before promoting to production.
