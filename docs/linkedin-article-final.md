# PipelineZero: What Shift-Left Security Looks Like in Practice

I hear the phrase “shift-left security” a lot, but most of the time it stays at a high level. People talk about secure development, DevSecOps, and catching issues early, but I wanted to understand what that actually looks like when it’s built into a real workflow.

A lot of teams still deal with security later in the process. That might mean testing close to launch, scanning after deployment, or reviewing things once the application is already live. By then, even small issues can take much more time and effort to fix.

So I built PipelineZero to see what a more proactive approach looked like in practice: a CI/CD pipeline with multiple security checks built directly into the development and deployment process for a live Azure-hosted application.

This was not just a demo project sitting in a repository. I wanted something I could actually run, troubleshoot, improve, and learn from. 

## What the Pipeline Does

My goal was not to pile on as many tools as possible. I wanted each part of the pipeline to have a clear purpose. At a high level, the pipeline checks:

- application code for common security issues

- dependencies and packages for known risk

- infrastructure configuration before deployment

- the live application after staging deployment

- deployment health before anything moves forward

That gave me layered coverage across the code, the cloud setup, and the running application itself.

## Architecture Overview

> **[INSERT ARCHITECTURE DIAGRAM HERE]***Suggested diagram: GitHub → security gates → staging deploy on Azure → post-deploy validation → production promotion path. Include ContractFlow frontend/backend, Key Vault, PostgreSQL, Redis, Blob Storage, and Container Apps.*Location: `docs/screenshots/demo/[architecture-diagram-file]`

## Security Checks Built Into the Workflow

I used five security tools in the pipeline, each focused on a different area. Some checks run during pull requests so issues can be caught before code is merged. Others run during deployment or after the application is live in staging.

### Gate 1: Semgrep (Pattern-Based SAST)

Semgrep runs on every pull request and scans the repository for common vulnerability patterns in the application code. It’s fast, which makes it a good fit for PR gating. It catches issues like injection risks, authentication mistakes, and unsafe crypto usage early enough that they can be fixed before they ever land in the main branch.

### Gate 2: CodeQL (Semantic SAST)

Where Semgrep is great at fast pattern matching, CodeQL goes deeper. I run GitHub’s CodeQL analysis for both Python and JavaScript/TypeScript so it can do semantic analysis and trace risky data flows through the codebase. That gives me another layer of confidence for cases where context matters more than pattern matching alone.

> **[INSERT SCREENSHOT: ****`06-github-actions-all-workflows-20260315.png`****]***All 4 GitHub Actions workflows - security-gate, deploy-staging, dast-gate, and CodeQL - shown in the Actions tab.*Location: `contractflow/docs/portfolio/findings/screenshots/06-github-actions-all-workflows-20260315.png`

> **[INSERT SCREENSHOT: ****`11-security-gate-all-green.webp`****]***Security-gate workflow completing successfully with all 4 jobs green (sast-iac, trivy, codeql python, codeql js/ts).*Location: `docs/screenshots/demo/11-security-gate-all-green.webp`

### Gate 3: Trivy (Supply Chain and Secrets)

Trivy handles the filesystem and dependency side of things. It scans Dockerfiles, dependency manifests, and source files for CVEs, leaked secrets, and security misconfigurations. I configured it to fail only on HIGH and CRITICAL findings. That mattered a lot, because one of the fastest ways to get people to ignore security tooling is to drown them in low-risk noise.

> **[INSERT SCREENSHOT: ****`13-trivy-scan-output.webp`****]***Trivy filesystem scan output showing vulnerability database updates and scan execution.*Location: `docs/screenshots/demo/13-trivy-scan-output.webp`

### Gate 4: Checkov (Infrastructure as Code)

Checkov validates the Terraform before anything gets near Azure. It checks for issues around encryption, network exposure, access controls, logging, and other cloud security concerns. That gave me a way to shift security left not just in the application code, but in the infrastructure layer too.

### Gate 5: Nuclei (DAST)

The first four scanners focus on code and infrastructure definitions. Nuclei runs after staging deploys and scans the live application itself. That matters because some issues only show up once the app is actually running. Runtime behavior, exposed endpoints, HTTP misconfigurations, and SSL-related issues don’t always appear in static analysis. For this gate, I used HIGH/CRITICAL severity thresholds so a serious finding blocks production deployment.

> **[INSERT SCREENSHOT: ****`04-dast-nuclei-success-20260315.png`****]***Nuclei DAST scan completing with 0 high/critical findings - DAST gate PASSED.*Location: `contractflow/docs/portfolio/findings/screenshots/04-dast-nuclei-success-20260315.png`

> **[INSERT SCREENSHOT: ****`github-dast-nuclei-job-steps-all-green-20260315.png`****]***All DAST job steps green - install, template update, scan, gate evaluation, artifact upload.*Location: `contractflow/docs/portfolio/findings/screenshots/github-dast-nuclei-job-steps-all-green-20260315.png`

## Secure Deployment Approach

I also wanted the deployment model itself to follow better security practices.

GitHub Actions authenticates to Azure using OIDC federation, so there are no long-lived cloud credentials stored in GitHub. No service principal secret sitting in a repo or secrets store. Just short-lived federated authentication for the workflow.

> **[INSERT SCREENSHOT: ****`02-entra-oidc-federated-credentials-20260315.webp`****]***Entra ID federated credentials configuration - GitHub Actions OIDC trust for the main branch.*Location: `contractflow/docs/portfolio/findings/screenshots/02-entra-oidc-federated-credentials-20260315.webp`

Runtime secrets like database URLs, Redis connection strings, and CSRF secrets live in Azure Key Vault. The deploy workflow retrieves them at deploy time and masks them in logs.

The deployment also includes health checks. Both the backend and frontend have to return HTTP 200 before staging is considered healthy.

> **[INSERT SCREENSHOT: ****`github-staging-environment-secrets-8-20260315.png`****]***GitHub staging environment with 8 secrets - all injected from Key Vault, none hardcoded.*Location: `contractflow/docs/portfolio/findings/screenshots/github-staging-environment-secrets-8-20260315.png`

> **[INSERT SCREENSHOT: ****`github-deploy-staging-run10-job-steps-all-green-20260315.png`****]***Deploy-staging workflow run - all steps green including OIDC login, Key Vault fetch, Docker build/push, container update, and health checks.*Location: `contractflow/docs/portfolio/findings/screenshots/github-deploy-staging-run10-job-steps-all-green-20260315.png`

## The Application: ContractFlow

This pipeline gates a real application I built called ContractFlow, a contract lifecycle management platform. The stack is FastAPI on the backend, React 19 on the frontend, with PostgreSQL, Redis, Azure Blob Storage, and Azure Container Apps. It includes 25+ API endpoints across areas like auth, contracts, versioning, approvals, audit, and admin.

I wanted the security work to be attached to something real, not just a set of disconnected scanning jobs.

> **[INSERT SCREENSHOT: ****`02-dashboard.webp`****]***Dashboard showing 12 contracts across 5 status categories.*Location: `docs/screenshots/demo/02-dashboard.webp`

> **[INSERT SCREENSHOT: ****`10-api-swagger-docs.webp`****]***Swagger UI showing all 25+ API endpoints across health, auth, contracts, versions, approvals, audit, and admin.*Location: `docs/screenshots/demo/10-api-swagger-docs.webp`

## Application Security: Defense in Depth

The pipeline is one layer, but I also wanted the application architecture itself to reflect secure design choices. I documented those decisions in six Architecture Decision Records.

For authentication, I chose HTTP-only secure cookies instead of storing tokens in localStorage, mainly for better resistance to XSS-related token theft. Sessions are hashed server-side, rotated regularly, and paired with double-submit CSRF protection.

Rate limiting had to be designed for distributed infrastructure. In-memory rate limiters fall apart once you scale horizontally, so Redis enforces limits across replicas.

For file handling, the application validates MIME types server-side, enforces a 50 MB upload limit, and uses short-lived HMAC-signed SAS tokens for downloads instead of trusting file extensions or exposing storage directly.

## Azure Infrastructure

The infrastructure is fully defined in Terraform, with 26 Azure resources provisioned through code. That includes the application hosting, container registry, secrets management, database, cache, storage, and monitoring components needed to support the staging environment.

> **[INSERT SCREENSHOT: ****`01-azure-resource-group-20260315.png`****]***Azure Portal resource group showing all provisioned resources - Container Apps, ACR, Key Vault, PostgreSQL, Redis, Storage, Log Analytics.*Location: `contractflow/docs/portfolio/findings/screenshots/01-azure-resource-group-20260315.png`

## What Taught Me the Most: What Broke in the Real World

The most valuable part of the project was not just getting scans to pass. It was seeing what happened when the pipeline met real infrastructure, real deployment constraints, and real troubleshooting.

**OWASP ZAP turned into a dead end.** I originally started with ZAP for DAST, but the `zaproxy:stable` image ran into a Docker permission issue on `/zap/wrk/zap.yaml`. After spending too much time trying to work around it, I replaced it with Nuclei. That ended up being the right call for this project — faster, more reliable, and easier to tune.

**Checkov skip lists turned out to be part of the documentation.** Because I was working with lower-cost Azure SKUs in staging, some policy failures were legitimate exceptions rather than mistakes. ACR vulnerability scanning needs Premium. Some PostgreSQL backup options weren’t available on the SKU I was using. I ended up with 23 documented Checkov skips, each with a reason. That skip list became part of the security story rather than something hidden away.

**Azure regional quotas forced an architecture exception.** On a student/trial subscription, PostgreSQL Flexible Server quotas blocked my preferred region. I had to provision the database in `northcentralus` instead of `eastus2`, which broke the cleaner single-region design I originally wanted.

**Asyncpg SSL handling broke staging.** The async SQLAlchemy engine didn’t accept `sslmode=require` in the connection string the way I expected. The fix was to remove it from the URL and pass `connect_args={"ssl": True}` instead. Small detail, but it was enough to break the deployment until I tracked it down.

None of those issues showed up in mocked testing. They only showed up once the system ran against real Azure APIs and real infrastructure. That was probably the clearest reminder in the whole project that “works on my machine” is not a security strategy.

## What I Did Not Try to Overstate

I also wanted to be realistic about the boundaries of the project.

This project does not include a separate production environment yet. It deploys to a live staging environment, and the design supports future expansion, but I did not add extra complexity just to make the project sound bigger than it was.

I also didn’t write custom Semgrep rules for the application. I used Semgrep’s auto configuration, which is a good baseline, but a mature enterprise implementation would usually include organization-specific rules.

And while automated security checks are helpful, they are not a replacement for deeper human review. The pipeline improves coverage and catches issues earlier, but it does not pretend to solve everything.

## What I Took Away From It

The biggest lesson for me was simple:

Getting security tools to run is the easy part. Getting them to be useful is the real work.

The value came from putting checks in the right places, reducing noise, documenting exceptions clearly, and tying everything to a real deployment process. I also came away convinced that OIDC federation is worth the setup. Removing long-lived cloud credentials from CI/CD is one of those changes that improves security and reduces operational headache at the same time.

The rest is in the repo: [github.com/petershamoon/pipeline-zero](https://github.com/petershamoon/pipeline-zero)