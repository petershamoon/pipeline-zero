# ADR-0002: Microsoft Entra ID As Production Identity Provider

- Status: Accepted
- Date: 2026-03-06
- Decision Owners: Security + Platform + Product Engineering

## Context
The platform requires production-grade authentication with MFA readiness, enterprise policy controls, lifecycle governance, and low operational burden. Maintaining custom password reset/MFA/session controls for production is high-risk and unnecessary.

## Decision
Use Microsoft Entra ID for production authentication and authorization identity.

Production rules:
- SPA uses OIDC Authorization Code + PKCE.
- Backend validates issuer, audience, signature, expiry, and critical claims.
- Role mapping is derived from Entra app roles/groups to internal app roles.
- Local auth fallback remains available for local development/test only and is disabled in production.

## Consequences
### Positive
- Enterprise-grade identity controls and policy enforcement.
- Reduced custom auth attack surface in production.
- Better auditability for user lifecycle and sign-in events.

### Negative
- Requires tenant/app registration setup and role mapping discipline.
- Requires coordination with cloud owner (Manus) for tenant-side config.

## Implementation Split
- Codex/Claude: app integration, claim validation, role mapping, auth tests.
- Manus: Entra app registrations, redirect URIs, app roles/groups, tenant policy controls.

## Revisit Criteria
Re-evaluate only if product scope materially changes away from enterprise identity assumptions.
