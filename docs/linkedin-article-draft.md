# How I Built a Shift-Left Security Pipeline That Catches Vulnerabilities Before Code Reaches Staging

Most teams bolt security on at the end. A penetration test before launch. A vulnerability scan after deployment. Maybe a compliance audit once a quarter. By that point, you're paying to fix things that could have been caught in a pull request.

I built a pipeline with 5 security tools — each covering a distinct attack surface with zero overlap — that gates every merge and every production deployment.

---

## The Problem With "Security Later"

The cost of fixing a vulnerability scales exponentially the later you find it. A SQL injection caught during code review is a five-minute fix. The same vulnerability found in production is an incident response, a patch, a deployment, a postmortem, and probably a conversation with legal.

Most CI/CD pipelines look like this: lint, test, build, deploy. Security is either a separate process entirely, or it's a single scanner that people learn to ignore because it's noisy and never blocks anything.

I wanted to build a pipeline where security scanning is as integral as unit tests — where the PR can't merge until every scanner passes, and nothing reaches production without passing dynamic analysis against the live staging environment.

## The Pipeline

The project is called PipelineZero. The demo application is a contract lifecycle management platform (FastAPI, React 19, Azure), but the application is just the workload. The pipeline is the point.

Here's what happens on every pull request:

**4 scanners run in parallel as a security gate:**

1. **Semgrep** scans the full repo for application vulnerability patterns — injection flaws, auth bypasses, insecure crypto, OWASP Top 10
2. **CodeQL** runs GitHub's semantic analysis with a matrix build for both Python and JavaScript/TypeScript — this is the one that does real dataflow analysis and taint tracking
3. **Trivy** does a full filesystem scan for dependency CVEs, leaked secrets, and misconfigurations at HIGH/CRITICAL severity — one tool that replaces the need for separate dependency auditing and secret scanning tools
4. **Checkov** validates all Terraform code against security compliance rules — encryption, access controls, logging, network exposure

If any scanner fails, the PR can't merge.

**Before production deployment (manual pre-production gate):**

5. **Nuclei** runs DAST against the live staging URL — HTTP vulnerabilities, exposed endpoints, SSL issues, misconfigurations. It gates on HIGH/CRITICAL findings, meaning a critical vulnerability blocks the production deploy.

The key design decision: DAST runs as a pre-production gate, not after every staging deploy. Staging deploys are frequent and most don't introduce HTTP-layer vulnerabilities. DAST is slow. Running it on every push is noise. Running it before production is a gate that matters.

## Why 5 Tools, Not 8

An early version of this pipeline had 8 scanners. That's what happens when you pick tools from a checklist instead of thinking about coverage gaps.

Bandit does Python SAST — but Semgrep already covers that and more. Gitleaks does secret scanning — but Trivy already scans for secrets as part of its filesystem sweep. pip-audit checks Python dependency CVEs — but Trivy's vulnerability scanner already pulls from the same advisory databases.

Three tools doing work that was already covered. Removing them wasn't about having fewer tools — it was about having the right tools. Each of the 5 remaining scanners covers a surface that no other tool in the pipeline touches:

- Semgrep: pattern-based SAST (fast, broad)
- CodeQL: semantic SAST (deep, dataflow-aware)
- Trivy: supply chain + secrets + misconfig (one tool, three surfaces)
- Checkov: IaC compliance (Terraform-specific)
- Nuclei: DAST (live application testing)

## Zero-Trust Deployment

The deployment pipeline itself doesn't store any credentials. GitHub Actions authenticates to Azure through OIDC federation — short-lived tokens, no service principal secrets in GitHub, no `AZURE_CLIENT_SECRET` sitting in a secrets store.

Runtime secrets (database URLs, Redis connection strings, CSRF secrets) live in Azure Key Vault. The deploy workflow fetches them at deploy time and masks them in logs using GitHub's `::add-mask::` directive. They never appear in workflow output.

The deploy also gates on health checks — both the backend (`/health/ready`) and frontend (`/health`) must return HTTP 200 before staging is considered healthy.

## Defense in Depth at the Application Level

The pipeline catches vulnerabilities in code. But the application also implements its own security controls:

- **Cookie-based sessions** with SHA-256 hashed session IDs, HttpOnly/Secure/SameSite flags, and server-side rotation on every request
- **CSRF protection** using a double-submit pattern — token in cookie and header, validated against an HMAC hash
- **Redis-backed rate limiting** with a sliding window algorithm and automatic fallback to in-memory when Redis is unavailable
- **File upload validation** using python-magic for byte-level MIME detection (not just file extension), restricted to 5 allowed types with SHA-256 checksums
- **5-role RBAC** mapped from Microsoft Entra ID app roles — Viewer, Contributor, Approver, Admin, SuperAdmin

The application refuses to start in production if required security configuration is missing or uses default values. No "we'll fix that in prod" situations.

## What I Learned Building This

**Fewer tools, better coverage.** The instinct is to add more scanners. The reality is that overlapping tools create noise, slow down pipelines, and give a false sense of thoroughness. Five tools with distinct coverage is better than eight with overlap.

**Checkov skip lists are real.** When your staging environment uses Azure's Basic-tier SKUs (because you're not spending production money on a portfolio project), you'll have legitimate policy skips. ACR vulnerability scanning requires Premium. Geo-redundant Postgres backups aren't available on B1ms. I documented every skip with the exact reason — the skip list became its own form of security documentation.

**ZAP has a Docker permission bug.** I started with OWASP ZAP for DAST. The `zaproxy:stable` image has a known `PermissionError` on `/zap/wrk/zap.yaml` that's been open for months. Switched to Nuclei — faster, more reliable, and the template system is excellent for targeting specific vulnerability classes.

**False positive management is the real work.** Getting scanners to run is easy. Getting them to run without generating so much noise that people ignore them is the actual engineering challenge. Severity thresholds, scan scope restrictions, and skip lists with documented justifications are what make a security pipeline usable instead of just technically correct.

**OIDC federation is worth the setup.** No more rotating service principal secrets. No more "who has access to the GitHub secrets?" conversations. The federated credential just works, and you never have to think about credential rotation again.

## By the Numbers

- **5 scanners**, zero overlap — each covering a distinct attack surface
- **Zero stored credentials** in GitHub — OIDC federation end-to-end
- **15 Checkov rules** explicitly documented as staging-SKU exceptions
- **6 GitHub Actions workflows** covering lint, test, security, deploy, DAST, and branch policy
- **6 Architecture Decision Records** documenting security-relevant design choices
- **DAST as a pre-production gate** with automated severity gating

---

The repo is public: [github.com/petershamoon/PipelineZero](https://github.com/petershamoon/PipelineZero)

If you're thinking about integrating security scanning into your CI/CD pipeline, the biggest lesson is this: start with the gate. If scanners run but never block anything, nobody pays attention. Make them required checks that block the merge, document your skip lists honestly, and treat security findings with the same urgency as failing tests. That's what shift-left actually means in practice.

---

*#ShiftLeft #DevSecOps #GitHubActions #SecurityPipeline #CICD #CloudSecurity #Azure #SAST #DAST #InfrastructureAsCode*
