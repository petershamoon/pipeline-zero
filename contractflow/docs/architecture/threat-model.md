# Threat Model Summary

## Auth threats
- Token/session theft via XSS: mitigated by HttpOnly session cookie, no token storage in browser storage.
- CSRF on state mutation: mitigated by double-submit CSRF cookie/header check.
- Token forgery: mitigated by Entra issuer/audience/signature validation.

## File upload threats
- Extension spoofing: mitigated by server-side MIME detection.
- Malicious oversized payloads: mitigated by strict size cap before persistence.
- Unauthorized download: mitigated by signed short-lived download URL checks.

## Authorization threats
- BOLA/IDOR: mitigated by centralized role/object policy checks on contract-scoped resources.
- Privilege escalation: mitigated by admin-only endpoints and Entra role mapping.

## Operational threats
- Secret leakage in CI/logs: mitigated by Key Vault references and secret scanning gates.
- Unsafe release rollout: mitigated by staged deploy and manual production approval.
