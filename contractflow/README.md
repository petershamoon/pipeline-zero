# ContractFlow Implementation Workspace

Last updated: 2026-03-08

This directory contains the executable implementation for PipelineZero ContractFlow.

## Canonical documentation
- Repository-level handoff package: `../docs/handoff`
- Governance and execution plans: `../docs/governance`, `../docs/execution`
- Local implementation runbooks/threat model: `docs/runbooks`, `docs/architecture`

## Local development
1. Start dependencies and services:

```bash
docker compose up --build
```

2. Run migrations:

```bash
cd backend
alembic upgrade head
```

3. Bootstrap the first admin user (development only):

```bash
curl -X POST http://localhost:8000/api/v1/auth/bootstrap-admin \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"ChangeMe123!"}'
```

4. Open the frontend at `http://localhost:3000`.

## Verification commands
Backend:

```bash
cd backend
ruff check app tests
PYTHONPATH=. pytest -q tests
```

Frontend:

```bash
cd frontend
npm install
npm run lint
npm run typecheck
npm run test
npm run build
```

Terraform contract checks:

```bash
cd infra
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

## Jobs
- `jobs/expiration-job/main.py` marks active contracts as expired when `end_date` is past.
- `jobs/notification-job/main.py` collects contracts expiring in the next 14 days.
