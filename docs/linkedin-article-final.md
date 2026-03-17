# How I Built a Shift-Left Security Pipeline That Catches Vulnerabilities Before Code Reaches Staging

I keep hearing about "shift-left security," but the conversations always stay at the principle level: DevSecOps culture, developer enablement, continuous scanning. Important concepts, but none of it ever answered the question I actually cared about: what does this look like in code?

Most teams bolt security on at the end. A penetration test before launch. A vulnerability scan after deployment. Maybe a compliance audit once a quarter. By that point, you're paying to fix things that could have been caught in a pull request. The cost of fixing a vulnerability scales exponentially the later you find it. A SQL injection caught during code review is a five-minute fix. The same vulnerability found in production is an incident response, a patch, a deployment, a postmortem, and probably a conversation with legal.

I wanted to understand it deeply, and the best way I know how to learn something is to build with it. So I built a pipeline with 5 security tools — each covering a distinct attack surface with zero overlap — that gates every merge and every production deployment. Not a proof of concept in a notebook. A working pipeline gating a live Azure infrastructure deployment for a contract lifecycle management platform (FastAPI, React 19, Azure).

I used two AI agents to help me build it: Claude handled the application code and CI/CD workflows, while Manus owned the Azure infrastructure provisioning and operations. I'm not going to pretend I hand-wrote every line of the 10,500+ lines of code. That's not the point. The point is understanding what the controls mean when you have to make them work in production, and that's the part no AI tool can shortcut for you.

Here's what I learned.

## The Pipeline: 5 Tools, Zero Overlap

An early version of this pipeline had 8 scanners. That's what happens when you pick tools from a checklist instead of thinking about coverage gaps. Bandit does Python SAST — but Semgrep already covers that and more. Gitleaks does secret scanning — but Trivy already scans for secrets as part of its filesystem sweep. pip-audit checks Python dependency CVEs — but Trivy's vulnerability scanner already pulls from the same advisory databases.

Three tools doing work that was already covered. Removing them wasn't about having fewer tools — it was about having the right tools. Each of the 5 remaining scanners covers a surface that no other tool in the pipeline touches.

> **[INSERT SCREENSHOT: `06-github-actions-all-workflows-20260315.png`]**
> *All 4 GitHub Actions workflows — security-gate, deploy-staging, dast-gate, and CodeQL — shown in the Actions tab.*
> Location: `contractflow/docs/portfolio/findings/screenshots/06-github-actions-all-workflows-20260315.png`

### Gate 1: Semgrep (Pattern-Based SAST)
Semgrep runs on every pull request, scanning the full repository for application vulnerability patterns. It catches injection flaws, authentication bypasses, and insecure cryptography. Because it's pattern-based, it runs in seconds. If Semgrep finds a vulnerability, the PR cannot merge.

### Gate 2: CodeQL (Semantic SAST)
While Semgrep looks for patterns, CodeQL runs GitHub's semantic analysis with a matrix build for both Python and JavaScript/TypeScript. This does real dataflow analysis and taint tracking — following untrusted user input from the API router all the way down to the database query.

### Gate 3: Trivy (Supply Chain & Secrets)
Trivy handles the filesystem sweep. It scans the Dockerfiles, the `requirements.txt`, the `package.json`, and the raw code for dependency CVEs, leaked secrets, and misconfigurations. It's configured to fail the build only on HIGH or CRITICAL severity findings, preventing the pipeline from getting clogged with low-risk noise.

### Gate 4: Checkov (Infrastructure as Code)
Checkov validates all Terraform code against security compliance rules before it ever reaches Azure. It checks for encryption at rest, network exposure, logging configurations, and access controls.

> **[INSERT SCREENSHOT: `github-actions-all-workflows-overview-20260315.png`]**
> *Workflow runs overview showing security-gate and deploy-staging passing on main branch pushes.*
> Location: `contractflow/docs/portfolio/findings/screenshots/github-actions-all-workflows-overview-20260315.png`

### Gate 5: Nuclei (DAST)
The first four scanners run on the code. The fifth scanner runs on the deployed application. After the staging deployment succeeds, Nuclei runs a Dynamic Application Security Testing (DAST) scan against the live staging URL. It catches HTTP vulnerabilities, exposed endpoints, SSL issues, and misconfigurations that only exist at runtime. It gates on HIGH/CRITICAL findings, meaning a critical vulnerability blocks the production deploy.

> **[INSERT SCREENSHOT: `04-dast-nuclei-success-20260315.png`]**
> *Nuclei DAST scan completing with 0 high/critical findings — DAST gate PASSED.*
> Location: `contractflow/docs/portfolio/findings/screenshots/04-dast-nuclei-success-20260315.png`

> **[INSERT SCREENSHOT: `github-dast-nuclei-job-steps-all-green-20260315.png`]**
> *All DAST job steps green — install, template update, scan, gate evaluation, artifact upload.*
> Location: `contractflow/docs/portfolio/findings/screenshots/github-dast-nuclei-job-steps-all-green-20260315.png`

## Zero-Trust Deployment

The deployment pipeline itself doesn't store any credentials. GitHub Actions authenticates to Azure through OIDC federation — short-lived tokens, no service principal secrets in GitHub, no `AZURE_CLIENT_SECRET` sitting in a secrets store.

> **[INSERT SCREENSHOT: `02-entra-oidc-federated-credentials-20260315.webp`]**
> *Entra ID federated credentials configuration — GitHub Actions OIDC trust for the main branch.*
> Location: `contractflow/docs/portfolio/findings/screenshots/02-entra-oidc-federated-credentials-20260315.webp`

> **[INSERT SCREENSHOT: `2026-03-14-entra-app-roles-configured.webp`]**
> *Entra app roles configured — Super Admin, Approver, Contributor, Viewer mapped to RBAC.*
> Location: `contractflow/docs/portfolio/findings/screenshots/2026-03-14-entra-app-roles-configured.webp`

Runtime secrets (database URLs, Redis connection strings, CSRF secrets) live in Azure Key Vault. The deploy workflow fetches them at deploy time and masks them in logs using GitHub's `::add-mask::` directive. They never appear in workflow output.

> **[INSERT SCREENSHOT: `github-staging-environment-secrets-8-20260315.png`]**
> *GitHub staging environment with 8 secrets — all injected from Key Vault, none hardcoded.*
> Location: `contractflow/docs/portfolio/findings/screenshots/github-staging-environment-secrets-8-20260315.png`

The deploy also gates on health checks — both the backend (`/health/ready`) and frontend (`/health`) must return HTTP 200 before staging is considered healthy.

> **[INSERT SCREENSHOT: `github-deploy-staging-run10-job-steps-all-green-20260315.png`]**
> *Deploy-staging workflow run — all steps green including OIDC login, Key Vault fetch, Docker build/push, container update, and health checks.*
> Location: `contractflow/docs/portfolio/findings/screenshots/github-deploy-staging-run10-job-steps-all-green-20260315.png`

## The Application: ContractFlow

The security pipeline gates a real application — ContractFlow, a contract lifecycle management platform. FastAPI backend, React 19 frontend, PostgreSQL, Redis, Azure Blob Storage. 25+ API endpoints across 6 resource groups (auth, contracts, versions, approvals, audit, admin).

> **[INSERT SCREENSHOT: `01-login-page.webp`]**
> *ContractFlow login page — local auth for development, Entra ID for production.*
> Location: `docs/screenshots/demo/01-login-page.webp`

> **[INSERT SCREENSHOT: `02-dashboard.webp`]**
> *Dashboard showing 12 contracts across 5 status categories.*
> Location: `docs/screenshots/demo/02-dashboard.webp`

> **[INSERT SCREENSHOT: `03-contracts-list.webp`]**
> *Contracts list with status badges, values, pagination — sortable by any column.*
> Location: `docs/screenshots/demo/03-contracts-list.webp`

> **[INSERT SCREENSHOT: `04-contract-detail.webp`]**
> *Contract detail view — Azure Enterprise Agreement ($245K) with version history and approval chains.*
> Location: `docs/screenshots/demo/04-contract-detail.webp`

> **[INSERT SCREENSHOT: `07-admin-audit-log.webp`]**
> *Audit log showing every action — login, create, approve, status_change, upload — with actor IDs and timestamps.*
> Location: `docs/screenshots/demo/07-admin-audit-log.webp`

> **[INSERT SCREENSHOT: `10-api-swagger-docs.webp`]**
> *Swagger UI showing all 25+ API endpoints across health, auth, contracts, versions, approvals, audit, and admin.*
> Location: `docs/screenshots/demo/10-api-swagger-docs.webp`

## Application Security: Defense in Depth

The pipeline ensures the code is safe, but the application architecture itself implements defense in depth. I documented these decisions in 6 Architecture Decision Records (ADRs).

**Cookie-Based Sessions (ADR-0004):** Browser auth state needs to be secure and resist XSS/CSRF attacks. Storing tokens in localStorage exposes them to script injection. The app uses HTTP-only, secure cookies with strict SameSite policies. Sessions are hashed server-side, rotated on every request, and paired with double-submit CSRF tokens.

**Distributed Rate Limiting (ADR-0005):** Multi-replica Container Apps deployment needs consistent rate limiting across instances. In-memory rate limiters are scoped to a single process. The app uses Redis to enforce global limits when the API scales horizontally.

**File Upload Security (ADR-0006):** Contract file uploads must be validated server-side to prevent malicious file storage. Relying on file extensions alone is trivially spoofable. The app validates MIME types, enforces a 50MB size limit, and uses short-lived HMAC-signed SAS tokens for secure downloads.

> **[INSERT SCREENSHOT: `06-admin-users.webp`]**
> *RBAC user management — 4 users across Super Admin, Approver, Contributor, and Viewer roles, mapped to 4 departments.*
> Location: `docs/screenshots/demo/06-admin-users.webp`

## Azure Infrastructure

The entire infrastructure is defined in Terraform — 26 resources across a single module.

> **[INSERT SCREENSHOT: `01-azure-resource-group-20260315.png`]**
> *Azure Portal resource group showing all provisioned resources — Container Apps, ACR, Key Vault, PostgreSQL, Redis, Storage, Log Analytics.*
> Location: `contractflow/docs/portfolio/findings/screenshots/01-azure-resource-group-20260315.png`

## The Part I Didn't Expect: What Broke in the Real World

I tested the full system end-to-end against a live Azure environment. The automated tests weren't the interesting part. The interesting part was what broke when the pipeline met real infrastructure.

**ZAP has a Docker permission bug.** I started with OWASP ZAP for DAST. The `zaproxy:stable` image has a known `PermissionError` on `/zap/wrk/zap.yaml` that's been open for months. I spent hours trying to `chmod 777` the workspace before realizing the tool itself was the blocker. I switched to Nuclei — it was faster, more reliable, and the template system was excellent for targeting specific vulnerability classes.

**Checkov skip lists are real.** When your staging environment uses Azure's Basic-tier SKUs (because you're not spending production money on a portfolio project), you'll have legitimate policy skips. ACR vulnerability scanning requires Premium. Geo-redundant Postgres backups aren't available on B1ms. I ended up with 23 explicitly documented Checkov skip rules. I documented every skip with the exact reason — the skip list became its own form of security documentation.

**PostgreSQL Regional Quotas.** Azure student/trial subscriptions have strict regional quotas for PostgreSQL Flexible Server. `eastus2` was blocked. The database had to be successfully provisioned in `northcentralus` as a documented exception, breaking my clean single-region architecture.

**Asyncpg SSL handling.** The async SQLAlchemy engine crashed because it doesn't accept the `sslmode=require` query parameter in the connection string. I had to strip it from the URL and pass `connect_args={"ssl": True}` instead. A tiny detail that completely broke the staging deployment until fixed.

Every single one of these bugs was invisible until the system ran against real Azure APIs with real infrastructure. If I had only relied on mocked tests, I would have shipped this thinking it was clean. "It works on my machine" has never been a testing strategy.

## What I Didn't Build

This section might be the most important part of the whole project. Understanding the boundaries of what you've built is part of the governance exercise.

**No production environment.** The pipeline deploys to a live staging environment, but the production environment is deferred. The architecture is designed for it, but I didn't provision the duplicate resources to save costs.

**No custom Semgrep rules.** I relied on the `--config auto` flag for Semgrep, which pulls from their community registry. A true enterprise deployment would include custom rules tailored to the organization's specific frameworks and internal APIs.

**No third-party penetration testing.** The DAST scanner catches low-hanging fruit, but it doesn't replace a human penetration tester finding complex business logic flaws.

## What I Took Away From This

**Fewer tools, better coverage.** The instinct is to add more scanners. The reality is that overlapping tools create noise, slow down pipelines, and give a false sense of thoroughness. Five tools with distinct coverage is better than eight with overlap.

**False positive management is the real work.** Getting scanners to run is easy. Getting them to run without generating so much noise that people ignore them is the actual engineering challenge. Severity thresholds, scan scope restrictions, and skip lists with documented justifications are what make a security pipeline usable instead of just technically correct.

**OIDC federation is worth the setup.** No more rotating service principal secrets. No more "who has access to the GitHub secrets?" conversations. The federated credential just works, and you never have to think about credential rotation again.

The full repository is on GitHub: [github.com/petershamoon/pipeline-zero](https://github.com/petershamoon/pipeline-zero)

If you're thinking about integrating security scanning into your CI/CD pipeline, the biggest lesson is this: start with the gate. If scanners run but never block anything, nobody pays attention. Make them required checks that block the merge, document your skip lists honestly, and treat security findings with the same urgency as failing tests. That's what shift-left actually means in practice.

#ShiftLeft #DevSecOps #GitHubActions #SecurityPipeline #CICD #CloudSecurity #Azure #SAST #DAST #InfrastructureAsCode
