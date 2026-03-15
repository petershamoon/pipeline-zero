# Network And Ingress Specification

Last updated: 2026-03-08

## Ingress requirements
| Service | Exposure | Auth requirement | Allowed sources | Source of truth | Validation |
|---|---|---|---|---|---|
| Frontend Container App | Public HTTPS | Public UI | Internet | deploy workflow + Container App ingress | load homepage + `/health` |
| Backend Container App | Private preferred (public allowed with restrictions in staging) | bearer/session auth | frontend origin + approved internal sources | app CORS config + Container App ingress | `/health/ready` + authenticated API call |
| Postgres | Private only | n/a | backend + job subnets only | Terraform network policy | connection from app only |
| Redis | Private only | n/a | backend + jobs only | Terraform network policy | redis ping from app |
| Blob | No public blob access | signed URL reads only | backend identity | storage account public access disabled | upload + signed download test |

## CORS contract
- `ALLOWED_ORIGINS` must include only trusted frontend origins.
- Wildcard origins are forbidden.

## Current baseline
- Local dev frontend: `http://localhost:3000`
- Local dev backend API: `http://localhost:8000/api/v1`
- Staging/prod origins are defined in `infra/envs/*/terraform.tfvars.example` and must be finalized by Manus after apply.

## TLS and domain
- HTTPS required for all public cloud endpoints.
- Enforce TLS 1.2+.
- Custom domain is optional for first staging release; generated domain is acceptable for staging validation.

## Network policy controls
- Deny broad public exposure for data-tier resources.
- Prefer private endpoints where feasible.
- Document any temporary exception with expiration date and owner.

## Validation checklist
- Preflight CORS request succeeds only from trusted origin.
- Backend is not reachable from untrusted sources if private ingress is enabled.
- Postgres/Redis/Blob do not expose broad public ingress.

## Open items
- *RESOLVED (2026-03-15)*: Staging ingress mode for backend container app is set to **restricted public** (`external = true`) to allow GitHub Actions DAST scanning and health checks to reach the API directly. CORS is strictly enforced via `ALLOWED_ORIGINS`.
- `BLOCKED` (Owner: Pete/Claude, Due: 2026-03-22): finalize production DNS/custom domain and certificate management path.

## Rollback/fallback notes
- If private ingress blocks staging validation, allow temporary restricted public ingress in staging with owner and expiration date recorded.
- If a production ingress change causes outage, revert to last known-good ingress profile and certificate binding.
