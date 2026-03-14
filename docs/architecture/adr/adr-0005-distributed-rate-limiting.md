# ADR-0005: Distributed Rate Limiting Via Redis

- Status: Accepted
- Date: 2026-03-06
- Decision Owners: Platform + Product Engineering

## Context
Multi-replica Container Apps deployment needs consistent rate limiting across instances. In-memory rate limiters are scoped to a single process and cannot enforce global limits when the API scales horizontally.

## Decision
Use a Redis-backed distributed rate limiter for API endpoints.

Rules:
- Auth endpoints (login, token refresh) enforce per-IP rate limits.
- Authenticated API endpoints enforce per-user rate limits.
- Rate limit counters are shared across all replicas via Redis.
- Limits are configurable per endpoint category without redeployment.

## Consequences
### Positive
- Rate limits are consistent across all replicas regardless of scaling.
- Rate limit state survives container restarts and redeployments.
- Centralized visibility into rate limit metrics.

### Negative
- Introduces Redis as a runtime dependency.
- Additional network latency per request for limit checks.

## Guardrails
- Fallback to in-memory rate limiting if Redis is unavailable in dev/test environments.
- Alert on Redis connection failures in production.
- Rate limit headers (X-RateLimit-Remaining, Retry-After) returned on all limited endpoints.
- Log and alert on sustained limit breaches for abuse detection.

## Revisit Criteria
Re-evaluate if request volume outgrows single-Redis capacity or if an API gateway with native rate limiting is introduced.
