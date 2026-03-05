# Architecture

This repository is a **local, deterministic** demonstration of how to reduce risk when shipping ML/LLM features:

- **Reproducibility & drift control**: environment parity checks + immutable build manifests.
- **Delivery safety**: CI/CD quality gates + promotion/rollback policy validation.
- **Reliability under on-call pressure**: SLO/alert/runbook readiness + ML-specific incident patterns.

## Data flow

1. `examples/*.toml` define:
   - Environment constraints (IaC/runtime parity signals)
   - ML delivery pipeline metadata (artifacts, gates, release policy)
   - Reliability posture (SLOs, alerts, runbooks, mitigations)
2. `portfolio_proof` loads TOML using `tomllib` (Python 3.11+).
3. Checks run deterministically and produce:
   - `artifacts/report.md` (human-readable)
   - `artifacts/report.json` (machine-readable)

## Threat model notes (practical)

- **Secrets leakage**: config may reference secrets; report generation must never print tokens.
- **Supply chain**: container images must be pinned by digest; model artifacts must be checksummed.
- **Prompt injection / data exfiltration** (LLMs): guardrails must exist (input filtering, tool allowlists, output constraints).
- **Training/serving skew**: drift and mismatch between training and production environments must be detectable.
- **Operational failure modes**: pipeline flakiness, bad deploys, drift/hallucinations, cost blowups.

