# Portfolio Demo Pack

This folder stores real, recorded security and quality evidence from normal development.

## Required artifacts
- Scanner catches (Semgrep/Trivy/CodeQL/Gitleaks/Checkov) with timestamps.
- CI gate failures that blocked merge/promotion.
- Before/after remediation diffs.
- DAST reports from staging scans.

## Structure
- `findings/`: individual finding records and screenshots.
- `walkthrough.md` (create when preparing a live demo): step-by-step narrative with linked evidence.
