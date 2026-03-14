# ADR-0003: Externalize Scheduled Workloads Into Azure Jobs

- Status: Accepted
- Date: 2026-03-06
- Decision Owners: Product Engineering + Platform

## Context
Contract expiration checks and notification jobs are periodic workloads. Running perpetual schedulers inside API startup/lifespan causes duplicate execution in multi-replica environments and complicates reliability.

## Decision
Run scheduled workloads outside API runtime using Azure Container Apps Jobs (or equivalent managed scheduler).

Rules:
- API process does not run perpetual cron loops.
- Jobs are idempotent and safe under retries.
- Job execution emits observability events and alerts.

## Consequences
### Positive
- No duplicate work from horizontal API scaling.
- Clear operational ownership and run visibility.
- Better retry/failure isolation for non-request workloads.

### Negative
- Extra deployment artifact and schedule configuration required.
- Requires runbook for job failures and replay.

## Guardrails
- Use idempotency keys per execution window.
- Track last successful run metadata.
- Alert on missed schedules and repeated failures.

## Revisit Criteria
Re-evaluate if workload volume demands dedicated worker runtime or queue-driven architecture.
