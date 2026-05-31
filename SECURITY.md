# Security Policy

This project handles user-submitted text and article URLs, calls an LLM provider, and can render generated HTML to images. Please treat prompt safety, input handling, and credential handling seriously.

## Supported Versions

Security fixes are considered for the latest public release and the current `main` branch.

| Version | Supported |
| --- | --- |
| v0.1.x | Yes |

## Reporting a Vulnerability

Please do not open a public GitHub issue for vulnerabilities.

Contact the maintainer through GitHub:

- https://github.com/359392475-blue-sky

Include:

- A short description.
- Reproduction steps.
- Affected version or commit.
- Potential impact.
- Suggested fix, if known.

## In Scope

- API key leakage.
- Unsafe file or image handling.
- HTML rendering issues with security impact.
- Server-side request handling issues.
- Bypass of required satire labels or warning injection.

## Out of Scope

- General disagreement with generated satire tone.
- Incorrect claims in generated output without a security impact.
- Public deployment hardening for environments not described in the README.
