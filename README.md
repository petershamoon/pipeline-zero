# PipelineZero

**Shift-left security pipeline that catches vulnerabilities before code reaches staging.**

PipelineZero is a reference implementation showing how to integrate 7 security scanners + DAST into GitHub Actions so every pull request is scanned for vulnerabilities, secrets, dependency CVEs, and infrastructure misconfigurations — and nothing merges without passing all of them.

ContractFlow (a contract lifecycle management app built with FastAPI and React 19) serves as the realistic workload. The security pipeline is the product.

---

## Security Pipeline Architecture

```
PR opened
  │
  ├─── ci-lint-test ──────── Lint + unit tests (backend & frontend)
  │
  ├─── security-gate ─────── 7 scanners in parallel:
  │      ├── Semgrep          SAST (application vuln patterns)
  │      ├── Bandit           SAST (Python-specific)
  │      ├── CodeQL           Semantic analysis (Python + JS/TS)
  │      ├── pip-audit        Dependency CVEs
  │      ├── Trivy            Vuln + secret + misconfig scanning
  │      ├── Gitleaks         Hardcoded secrets in repo
  │      └── Checkov          Terraform/IaC compliance
  │
  └─── branch-policy ─────── PR description enforcement

Merge to main
  │
  └─── deploy-staging ─────── OIDC auth → Key Vault secrets → build → deploy → health checks
         │
         └─── dast-gate ────── Nuclei DAST against live staging (gates on HIGH/CRITICAL)
```

## The 8 Scanners

### Static Application Security Testing (SAST)

| Scanner | What It Catches | Scope |
|---------|----------------|-------|
| **Semgrep** | Injection flaws, auth bypasses, insecure crypto, OWASP Top 10 patterns | Full repo (`--config auto`) |
| **Bandit** | Python-specific issues: `eval()`, hardcoded passwords, weak hashing, SQL injection | `contractflow/backend/app` |
| **CodeQL** | Semantic dataflow analysis — taint tracking, type confusion, API misuse | Python + JavaScript/TypeScript (matrix build) |

### Supply Chain Security

| Scanner | What It Catches | Scope |
|---------|----------------|-------|
| **pip-audit** | Known CVEs in Python dependencies (PyPI advisory database) | `requirements.txt` |
| **Trivy** | Filesystem vulnerabilities, leaked secrets, misconfigurations | Full repo (severity: HIGH, CRITICAL) |

### Secrets & Infrastructure

| Scanner | What It Catches | Scope |
|---------|----------------|-------|
| **Gitleaks** | API keys, tokens, passwords, private keys in source code | Full repo (v8.30.0) |
| **Checkov** | Terraform misconfigurations: missing encryption, public access, missing logging | `contractflow/infra` |

### Dynamic Application Security Testing (DAST)

| Scanner | What It Catches | Scope |
|---------|----------------|-------|
| **Nuclei** | HTTP vulnerabilities, exposed endpoints, SSL issues, misconfigurations against running app | Live staging URL (medium/high/critical severity gate) |

## Zero-Credential Deployment

No service principal secrets are stored in GitHub. The deployment pipeline uses OIDC federation end-to-end:

```
GitHub Actions ──OIDC token──→ Azure AD ──federated credential──→ Azure subscription
                                                                        │
                                                            ┌───────────┴───────────┐
                                                            │                       │
                                                      Key Vault               Container Apps
                                                      fetch secrets            deploy images
                                                            │
                                                    ┌───────┴───────┐
                                                    │       │       │
                                              DATABASE_URL  │  CSRF_SECRET
                                                      REDIS_URL
```

- **OIDC federation**: GitHub Actions authenticates to Azure via short-lived OIDC tokens — no `AZURE_CLIENT_SECRET` anywhere
- **Key Vault injection**: `DATABASE_URL`, `REDIS_URL`, and `CSRF_SECRET` are fetched from Azure Key Vault at deploy time and masked in workflow logs (`::add-mask::`)
- **Health check gates**: Backend and frontend must return HTTP 200 on `/health/ready` and `/health` respectively before the pipeline proceeds to DAST
- **Environment protection**: Staging and production are separate GitHub environments with protection rules
- **Concurrency locks**: `cancel-in-progress: false` prevents parallel deploys from corrupting state

## Application Security (Defense in Depth)

The application layer implements its own security controls independent of the pipeline:

| Control | Implementation |
|---------|---------------|
| **Session management** | Cookie-based with SHA-256 hashed session IDs, HttpOnly/Secure/SameSite=Lax, server-side rotation on every request |
| **CSRF protection** | Double-submit pattern — CSRF token in cookie + header, validated against HMAC hash |
| **Rate limiting** | Redis-backed sliding window with automatic fallback to in-memory when Redis is unavailable |
| **File upload validation** | python-magic byte-level MIME detection (not just extension), 5 allowed types, SHA-256 checksums, 50MB limit |
| **Authentication** | Microsoft Entra ID in production with OIDC/MSAL, local dev auth with automatic disable in production |
| **Authorization** | 5-role RBAC (Viewer → Contributor → Approver → Admin → SuperAdmin) mapped from Entra app roles |
| **Production fail-fast** | App refuses to start if required Entra config, Key Vault URI, or CSRF secret is missing/default |

## Infrastructure as Code

All Azure resources are defined in Terraform with Checkov compliance:

| Resource | Configuration |
|----------|--------------|
| Container Apps Environment | Log Analytics integration, user-assigned managed identity |
| Azure Container Registry | Admin disabled, RBAC-only access via managed identity |
| Key Vault | Purge protection enabled, RBAC authorization, network ACLs default-deny with AzureServices bypass |
| Storage Account | TLS 1.2 minimum, public access disabled, blob + queue logging enabled |
| PostgreSQL Flexible Server | v16, automated backups, SSL required |
| Redis Cache | TLS 1.2 minimum |
| Managed Identity | Single identity shared across backend + jobs with least-privilege role assignments (Key Vault Secrets User, Storage Blob Data Contributor, AcrPull) |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui, React Hook Form + Zod |
| Database | PostgreSQL 16 (asyncpg driver) |
| Cache | Redis (session store + rate limiting) |
| Storage | Azure Blob Storage (contract documents) |
| Auth | Microsoft Entra ID (MSAL.js + MSAL Python) |
| IaC | Terraform (~> 4.0 azurerm provider) |
| CI/CD | GitHub Actions (6 workflows) |
| Containers | Docker, Azure Container Apps |

## Quick Start (Local Development)

```bash
# Clone and start infrastructure
git clone https://github.com/petershamoon/PipelineZero.git
cd PipelineZero/contractflow
docker compose up -d  # PostgreSQL, Redis, Azurite

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

The app is available at `http://localhost:3000` with the backend API at `http://localhost:8000`.

## CI/CD Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci-lint-test` | PR to main, push to main | Lint (ruff + eslint) + unit tests (pytest + vitest) + typecheck |
| `security-gate` | PR to main, push to main | Run all 7 security scanners, upload SAST artifacts |
| `branch-policy` | PR to main | Enforce non-empty PR descriptions |
| `deploy-staging` | Push to main, manual | OIDC login → Key Vault fetch → Docker build/push → Container App update → health checks |
| `dast-gate` | After deploy-staging, manual | Nuclei DAST scan against staging, gate on HIGH/CRITICAL findings |
| `deploy-production` | Manual only | OIDC login → deploy same image SHA to production environment |

## Project Structure

```
PipelineZero/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Lint + test gate
│   │   ├── security.yml              # 7-scanner security gate
│   │   ├── dast.yml                  # Nuclei DAST post-deploy
│   │   ├── deploy-staging.yml        # OIDC + Key Vault + deploy
│   │   ├── deploy-production.yml     # Manual production deploy
│   │   └── branch-policy.yml         # PR description enforcement
│   └── pull_request_template.md      # Security checklist template
├── contractflow/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── api/                  # FastAPI route handlers
│   │   │   ├── core/                 # Config, database, security, auth
│   │   │   ├── models/               # SQLAlchemy models
│   │   │   ├── repositories/         # Data access layer
│   │   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── services/             # Business logic
│   │   │   └── workers/              # Background task processing
│   │   ├── migrations/               # Alembic database migrations
│   │   ├── tests/
│   │   │   ├── unit/                 # No database required
│   │   │   ├── integration/          # Requires PostgreSQL
│   │   │   └── security/             # Auth and access control tests
│   │   └── Dockerfile
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── components/           # React components (shadcn/ui)
│   │   │   ├── pages/                # Route pages
│   │   │   ├── services/             # API client layer
│   │   │   ├── store/                # Zustand state management
│   │   │   └── hooks/                # Custom React hooks
│   │   └── Dockerfile
│   ├── infra/
│   │   ├── modules/platform/         # Terraform module (all Azure resources)
│   │   └── envs/                     # staging + production variable files
│   ├── jobs/                         # Scheduled Container App Jobs
│   ├── semgrep-rules/                # Custom Semgrep rules + tests
│   └── docker-compose.yml            # Local dev (Postgres, Redis, Azurite)
└── docs/
    ├── architecture/adr/             # Architecture Decision Records
    ├── governance/                   # Branch protection policies
    └── handoff/                      # Azure operations handoff docs
```

## Architecture Decision Records

| ADR | Decision | Status |
|-----|----------|--------|
| [ADR-0001](docs/architecture/adr/adr-0001-modular-monolith.md) | Modular monolith as baseline architecture | Accepted |
| [ADR-0002](docs/architecture/adr/adr-0002-entra-id-production-auth.md) | Microsoft Entra ID as production identity provider | Accepted |
| [ADR-0003](docs/architecture/adr/adr-0003-external-scheduled-jobs.md) | Externalize scheduled workloads into Azure Container App Jobs | Accepted |
| [ADR-0004](docs/architecture/adr/adr-0004-cookie-session-model.md) | Cookie-based session model for browser auth | Accepted |
| [ADR-0005](docs/architecture/adr/adr-0005-distributed-rate-limiting.md) | Distributed rate limiting via Redis | Accepted |
| [ADR-0006](docs/architecture/adr/adr-0006-file-upload-security.md) | Server-side file upload validation and secure download | Accepted |

## Demo Approach

Portfolio demos use recorded real findings captured during normal development — scanner catches, before/after diffs, CI gate failures. No intentionally vulnerable code lives in this repository.
