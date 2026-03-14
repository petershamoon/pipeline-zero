# Key Rotation and Credential Lifecycle Policy

## Scope
- Application secrets: `DATABASE_URL`, `REDIS_URL`, `CSRF_SECRET`, storage credentials.
- Identity credentials and federated trust configuration.

## Rotation standards
- Regular rotation: every 90 days minimum.
- Emergency rotation: within 4 hours of confirmed compromise.
- Production secrets are managed in Key Vault only.

## Rotation workflow
1. Generate replacement secret in Key Vault.
2. Update staging references and run smoke tests.
3. Promote to production with approval gate.
4. Invalidate old credentials and verify no stale consumers.

## Validation
- Backend health check, auth login flow, and critical API smoke pass.
- Audit event confirms credential update action.
- Alerts remain clear during post-rotation quiet period.
