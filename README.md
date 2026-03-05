# 54-iac-delivery-incident-reproducibility

Portfolio repo that demonstrates **reproducible ML/LLM delivery with guardrails**, focused on:

1) **Reproducibility + drift control** (config parity across environments, immutable artifacts, deterministic manifests).
2) **Delivery safety** (CI/CD quality gates, promotion rules, rollback-ready release plans).
3) **Operational reliability** (drift + hallucination risk mitigations, SLOs/alerts, runbook-ready incident response).

## Architecture (inputs → checks → outputs → runbooks)

- Inputs: TOML configs under `examples/`
- Checks: `python -m portfolio_proof validate` enforces key controls
- Outputs: `python -m portfolio_proof report` writes `artifacts/report.md`
- Runbooks: `docs/runbooks/` maps each finding to concrete response steps

## Quick start

```bash
make setup
make demo
```

Open `artifacts/report.md` to see:
- Risks found (by severity)
- Validation results
- Guardrails + the exact runbook(s) to follow

## Demo (what to look for)

The generated report ties back to the 3 pain points:
- **Infrastructure / environment drift**: compares dev/staging/prod IaC+runtime constraints and flags drift.
- **Release friction / risky rollouts**: verifies model promotion gates, canary/rollback policy, and CI requirements.
- **On-call reliability**: checks SLOs/alerts/runbooks and ML-specific risks (model drift + hallucinations).

Want to see failures? Try the intentionally broken examples:

```bash
PYTHONPATH=src python3 -m portfolio_proof validate --examples examples/bad
```

## Security (by design)

- No secrets are required for the demo.
- `artifacts/`, `.env*`, keys, credentials, and state files are gitignored.
- Any future real integrations should use **least privilege** and avoid logging tokens.

## Out of scope (intentionally)

- Running real Terraform/Kubernetes applies.
- Training real models (the repo focuses on delivery/reliability guardrails and reproducibility signals).
