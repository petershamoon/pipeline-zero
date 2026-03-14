# ADR-0006: Server-Side File Upload Validation And Secure Download

- Status: Accepted
- Date: 2026-03-06
- Decision Owners: Security + Product Engineering

## Context
Contract file uploads must be validated server-side to prevent malicious file storage. Relying on file extensions alone is trivially spoofable, and direct blob storage URLs without scoping expose files to unauthorized access.

## Decision
Validate and secure all file uploads and downloads server-side.

Rules:
- MIME type validation uses python-magic reading file bytes, not file extension.
- Maximum file size is enforced before persistence to storage.
- SHA-256 checksum is computed and stored alongside each file for integrity verification.
- Downloads are served via scoped, short-lived, read-only SAS URLs.
- Only allowlisted file types are accepted: PDF, DOCX, TXT, PNG, JPEG.

## Consequences
### Positive
- Extension spoofing is prevented by byte-level MIME detection.
- Checksums detect file corruption or tampering at rest.
- SAS URLs are time-limited and scoped to individual files.

### Negative
- python-magic requires libmagic system dependency in container images.
- SAS URL generation adds minor latency to download requests.

## Guardrails
- Strict allowlist enforcement: PDF, DOCX, TXT, PNG, JPEG only.
- Maximum upload size: 50 MB.
- SAS URL expiry: 15 minutes.
- Reject any file where detected MIME type does not match the allowlist.
- Log all upload attempts with file hash, size, and detected type for audit.

## Revisit Criteria
Re-evaluate if file type requirements expand significantly or if a dedicated antivirus/malware scanning pipeline is introduced.
