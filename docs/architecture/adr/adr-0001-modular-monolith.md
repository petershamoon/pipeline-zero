# ADR-0001: Modular Monolith As Baseline Architecture

- Status: Accepted
- Date: 2026-03-06
- Decision Owners: Product Engineering

## Context
ContractFlow needs to deliver secure contract lifecycle workflows quickly with a small implementation surface and strong operational clarity. The system has clear domains (auth, contracts, versions, approvals, admin, audit) but does not yet have scale or team topology that justifies service-per-domain overhead.

## Decision
Adopt a modular monolith architecture:
- Single backend deployable for core API behavior.
- Internal module boundaries with explicit service and repository layers.
- Shared database with strong schema and access constraints.
- Extract only truly independent workloads (scheduled jobs) outside API runtime.

## Consequences
### Positive
- Faster delivery velocity and simpler debugging.
- Lower infrastructure and operational complexity.
- Easier end-to-end security and transaction guarantees.

### Negative
- We must enforce boundaries through code review and tests.
- Future domain extraction requires careful contract definition.

## Guardrails
- No cross-module router imports.
- Domain logic in services, not endpoints.
- Object-level auth policy shared and tested centrally.

## Revisit Criteria
Re-evaluate if any of the following becomes true:
- Distinct teams need independent release cadence.
- Non-overlapping scaling profiles become dominant.
- Queue-heavy async domain grows beyond current API/process model.
