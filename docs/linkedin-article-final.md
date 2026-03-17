# How I Built a Shift-Left Security Pipeline That Catches Vulnerabilities Before Code Reaches Staging

I keep hearing about "shift-left security," but the conversations always stay at the principle level: DevSecOps culture, developer enablement, continuous scanning. Important concepts, but none of it ever answered the question I actually cared about: what does this look like in code?

Most teams bolt security on at the end. A penetration test before launch. A vulnerability scan after deployment. Maybe a compliance audit once a quarter. By that point, you're paying to fix things that could have been caught in a pull request. The cost of fixing a vulnerability scales exponentially the later you find it. A SQL injection caught during code review is a five-minute fix. The same vulnerability found in production is an incident response, a patch, a deployment, a postmortem, and probably a conversation with legal.

I wanted to understand it deeply, and the best way I know how to learn something is to build with it. So I built a pipeline with 5 security tools — each covering a distinct attack surface with zero overlap — that gates every merge and every production deployment. Not a proof of concept in a notebook. A working pipeline gating a live Azure infrastructure deployment for a contract lifecycle management platform (FastAPI, React 19, Azure).

I used two AI agents to help me build it: Claude handled the application code and CI/CD workflows, while Manus owned the Azure infrastructure provisioning and operations. I'm not going to pretend I hand-wrote every line of the 10,500+ lines of code. That's not the point. The point is understanding what the controls mean when you have to make them work in production, and that's the part no AI tool can shortcut for you.

Here's what I learned.

## The Pipeline: 5 Tools, Zero Overlap

An early version of this pipeline had 8 scanners. That's what happens when you pick tools from a checklist instead of thinking about coverage gaps. Bandit does Python SAST — but Semgrep already covers that and more. Gitleaks does secret scanning — but Trivy already scans for secrets as part of its filesystem sweep. pip-audit checks Python dependency CVEs — but Trivy's vulnerability scanner already pulls from the same advisory databases.

Three tools doing work that was already covered. Removing them wasn't about having fewer tools — it was about having the right tools. Each of the 5 remaining scanners covers a surface that no other tool in the pipeline touches:

1. **Semgrep**: Pattern-based SAST scanning the full repo for application vulnerability patterns (injection flaws, auth bypasses, insecure crypto).
2. **CodeQL**: Semantic SAST running GitHub's semantic analysis with a matrix build for both Python and JavaScript/TypeScript. This does real dataflow analysis and taint tracking.
3. **Trivy**: Supply chain, secrets, and misconfigurations. A full filesystem scan for dependency CVEs, leaked secrets, and misconfigurations at HIGH/CRITICAL severity.
4. **Checkov**: Infrastructure as Code compliance. Validates all Terraform code against security compliance rules (encryption, access controls, logging, network exposure).
5. **Nuclei**: Dynamic Application Security Testing (DAST). Runs against the live staging URL to catch HTTP vulnerabilities, exposed endpoints, SSL issues, and misconfigurations.

If any of the first four scanners fail, the PR cannot merge. The fifth scanner, Nuclei, runs as a pre-production gate. It gates on HIGH/CRITICAL findings, meaning a critical vulnerability blocks the production deploy.

## The Part I Didn't Expect: What Broke in the Real World

I tested the full system end-to-end against a live Azure environment. The automated tests weren't the interesting part. The interesting part was what broke when the pipeline met real infrastructure.

**ZAP has a Docker permission bug.** I started with OWASP ZAP for DAST. The `zaproxy:stable` image has a known `PermissionError` on `/zap/wrk/zap.yaml` that's been open for months. I spent hours trying to `chmod 777` the workspace before realizing the tool itself was the blocker. I switched to Nuclei — it was faster, more reliable, and the template system was excellent for targeting specific vulnerability classes.

**Checkov skip lists are real.** When your staging environment uses Azure's Basic-tier SKUs (because you're not spending production money on a portfolio project), you'll have legitimate policy skips. ACR vulnerability scanning requires Premium. Geo-redundant Postgres backups aren't available on B1ms. I ended up with 23 explicitly documented Checkov skip rules. I documented every skip with the exact reason — the skip list became its own form of security documentation.

**PostgreSQL Regional Quotas.** Azure student/trial subscriptions have strict regional quotas for PostgreSQL Flexible Server. `eastus2` was blocked. The database had to be successfully provisioned in `northcentralus` as a documented exception, breaking my clean single-region architecture.

**Asyncpg SSL handling.** The async SQLAlchemy engine crashed because it doesn't accept the `sslmode=require` query parameter in the connection string. I had to strip it from the URL and pass `connect_args={"ssl": True}` instead. A tiny detail that completely broke the staging deployment until fixed.

Every single one of these bugs was invisible until the system ran against real Azure APIs with real infrastructure. If I had only relied on mocked tests, I would have shipped this thinking it was clean. "It works on my machine" has never been a testing strategy.

## Zero-Trust Deployment

The deployment pipeline itself doesn't store any credentials. GitHub Actions authenticates to Azure through OIDC federation — short-lived tokens, no service principal secrets in GitHub, no `AZURE_CLIENT_SECRET` sitting in a secrets store.

Runtime secrets (database URLs, Redis connection strings, CSRF secrets) live in Azure Key Vault. The deploy workflow fetches them at deploy time and masks them in logs using GitHub's `::add-mask::` directive. They never appear in workflow output.

The deploy also gates on health checks — both the backend (`/health/ready`) and frontend (`/health`) must return HTTP 200 before staging is considered healthy.

## What I Took Away From This

**Fewer tools, better coverage.** The instinct is to add more scanners. The reality is that overlapping tools create noise, slow down pipelines, and give a false sense of thoroughness. Five tools with distinct coverage is better than eight with overlap.

**False positive management is the real work.** Getting scanners to run is easy. Getting them to run without generating so much noise that people ignore them is the actual engineering challenge. Severity thresholds, scan scope restrictions, and skip lists with documented justifications are what make a security pipeline usable instead of just technically correct.

**OIDC federation is worth the setup.** No more rotating service principal secrets. No more "who has access to the GitHub secrets?" conversations. The federated credential just works, and you never have to think about credential rotation again.

The full repository is on GitHub: [github.com/petershamoon/pipeline-zero](https://github.com/petershamoon/pipeline-zero)

If you're thinking about integrating security scanning into your CI/CD pipeline, the biggest lesson is this: start with the gate. If scanners run but never block anything, nobody pays attention. Make them required checks that block the merge, document your skip lists honestly, and treat security findings with the same urgency as failing tests. That's what shift-left actually means in practice.

#ShiftLeft #DevSecOps #GitHubActions #SecurityPipeline #CICD #CloudSecurity #Azure #SAST #DAST #InfrastructureAsCode
