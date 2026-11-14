# Security policy

HTMD 0.1 is a language **draft**, not a complete runtime. Its trust and execution model is specified in [docs/security.md](docs/security.md).

## Reporting an issue

Before a public repository host is configured, report suspected flaws privately to the repository maintainer using a secure contact channel of your choice. When GitHub security advisories become available, maintainers should enable **Private Vulnerability Reporting** for this repository and update this document with the correct contact method.

Do not include real credentials, private memory files, or exploit payloads containing personal data in public issues.

## Supported versions

| Version | Status |
| --- | --- |
| 0.1 draft | Under review; no production security support commitment |

## Scope

Security issues include parser confusion, path traversal, unauthorized context expansion, HTML injection, prompt-injection privilege escalation, and event-integrity bypass in implementations. The absence of a reference implementation means this repository cannot currently issue implementation security patches.
