# Security

## Controls demonstrated

- **No-secrets posture by default**: the demo runs without credentials.
- **Git hygiene**: state files, credentials, and generated artifacts are ignored.
- **Immutable artifacts**: image digests and checksums are validated in the example manifest.
- **Auditability**: a machine-readable report (`artifacts/report.json`) provides evidence of checks run and results.

## Least privilege guidance (for real deployments)

- Use scoped credentials for registries and deployment targets.
- Separate read-only CI credentials from production deploy credentials.
- Never log bearer tokens, API keys, or cloud session material.

## What this repo does not do

- It does not manage real cloud resources.
- It does not perform vulnerability scanning (no external tooling); instead it validates that scanning is a required gate.

