# Branch Protection and Environment Gates

Date: 2026-03-08

This policy defines branch safety and deployment gating for ContractFlow.

## Branch model
- `main`: production-intent branch, protected.
- `feature/*`: normal development branches.
- `hotfix/*`: urgent fixes.

## Required GitHub branch protections for `main`
- Require pull request before merging.
- Require at least 1 approval.
- Require conversation resolution before merge.
- Require status checks to pass before merge.
- Restrict who can push directly to `main`.
- Require signed commits (recommended).
- Disallow force pushes.
- Disallow branch deletion.

## Required status checks
- `ci-lint-test`
- `security-gate`
- `branch-policy`
- `dast-gate` (for deploy PRs/promotion flow as applicable)

## Workflow sources
- `.github/workflows/ci.yml`
- `.github/workflows/security.yml`
- `.github/workflows/branch-policy.yml`
- `.github/workflows/deploy-staging.yml`
- `.github/workflows/deploy-production.yml`
- `.github/workflows/dast.yml`

## Environment protection rules
### `staging`
- Manual approvals optional (recommended during early setup).
- Allow deploys from `main` and approved `feature/*` integration branches.

### `production`
- Manual approval required.
- Allowed branch: `main` only.

## Ownership
- Codex/Claude: codifies branch checks in workflows and PR templates.
- Manus: applies GitHub branch protection and environment settings.

## Validation checklist
- Attempt production deploy from non-`main`; confirm environment restriction blocks.
- Confirm direct push to `main` is denied for non-admin users.
