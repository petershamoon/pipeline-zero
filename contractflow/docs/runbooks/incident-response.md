# Incident Response Runbook

## Trigger conditions
- Elevated 5xx error rates or auth failures after deploy.
- Critical scanner findings in CI/security gates.
- Confirmed secret or credential compromise.

## Immediate actions
1. Declare incident and assign incident commander.
2. Freeze production deploys.
3. Roll back to last known-good revision.
4. Disable affected scheduled jobs if they mutate data incorrectly.

## Investigation checklist
- Correlate release SHA with first observed failures.
- Inspect audit logs for suspicious actor/action patterns.
- Validate Entra token claims and app role mappings.
- Verify Key Vault references and recent secret rotations.

## Recovery
1. Patch and validate in staging.
2. Re-run CI, security gate, and DAST gate.
3. Perform controlled production redeploy.
4. Monitor alert quiet period and close incident.

## Postmortem
- Document timeline, root cause, impact, and corrective actions.
- Track follow-up tickets with owners and due dates.
