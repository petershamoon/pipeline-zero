# ADR-0004: Cookie-Based Session Model For Browser Auth

- Status: Accepted
- Date: 2026-03-06
- Decision Owners: Security + Product Engineering

## Context
Browser auth state needs to be secure and resist XSS/CSRF attacks. Storing tokens in localStorage or sessionStorage exposes them to script injection, and manual token management in client-side JavaScript increases attack surface.

## Decision
Use HttpOnly/Secure/SameSite=Lax cookies for session management.

Rules:
- Never store authentication tokens in localStorage or sessionStorage.
- Server-side session IDs are stored hashed (not plaintext).
- CSRF protection uses the double-submit cookie pattern.
- Session cookies are marked HttpOnly, Secure, and SameSite=Lax.
- Session IDs are rotated on each use to limit replay window.

## Consequences
### Positive
- XSS attacks cannot steal session tokens via JavaScript.
- CSRF protection is built-in through SameSite and double-submit pattern.
- No client-side token management code required.

### Negative
- Requires CSRF middleware on all state-changing endpoints.
- Cookie management adds backend complexity for session lifecycle.

## Guardrails
- No bearer tokens exposed to browser JavaScript.
- Session IDs hashed server-side before storage.
- Session IDs rotated on every authenticated use.
- Audit for any localStorage/sessionStorage token usage in CI.

## Revisit Criteria
Re-evaluate if authentication model shifts to a stateless token-only architecture or if a BFF (Backend-for-Frontend) pattern is adopted.
