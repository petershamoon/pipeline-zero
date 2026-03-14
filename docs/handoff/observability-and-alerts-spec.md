# Observability And Alerts Specification

Last updated: 2026-03-08

## Logging
- Backend and jobs emit structured JSON logs.
- Minimum fields: `timestamp`, `level`, `service`, `message`.
- Target fields for cloud dashboards: `environment`, `correlation_id`, `user_id`, `request_path`, `status_code`.
- Sensitive fields must be redacted.

## Tracing
- FastAPI OpenTelemetry instrumentation hook is implemented.
- Correlation ID is propagated via request header (`X-Correlation-ID`) and response echo.

## Metrics
Required service-level metrics:
- API request count, latency p50/p95/p99, error rate.
- Auth failures and token validation failures.
- Upload success/failure and size distribution.
- Job execution count, duration, and failure rate.

## Alert thresholds (initial)
| Alert | Threshold | Severity | Owner | Validation |
|---|---|---|---|---|
| API error rate spike | >5% for 10 min | High | Manus | synthetic 5xx burst |
| API p95 latency | >1500ms for 15 min | Medium | Manus | load smoke |
| Job failures | 2 consecutive failures | High | Manus | fail one scheduled job intentionally |
| Failed login anomaly | >3x baseline in 30 min | Medium | Manus + Security | controlled auth failure burst |
| DB connection failures | sustained >5 min | High | Manus | simulated DB outage in staging |

## Dashboard minimums
- Service health dashboard (backend/frontend/jobs).
- Security dashboard (auth failures + denied access + suspicious spikes).
- Data dashboard (DB connectivity + query error trends).

## Implementation references
- `backend/app/telemetry/logging.py`
- `backend/app/telemetry/tracing.py`
- `backend/app/main.py` (correlation header middleware)

## Open items
- `BLOCKED` (Owner: Manus, Due: 2026-03-22): connect app/job logs and traces to Azure Monitor + Log Analytics dashboards.
- `BLOCKED` (Owner: Manus, Due: 2026-03-22): configure alert routing (on-call channel and escalation policy).

## Rollback/fallback notes
- If new alert rules generate excessive noise, revert to previous alert set and re-introduce threshold changes incrementally.
- If telemetry export causes runtime impact, disable non-critical exporters first and retain application health logging.
