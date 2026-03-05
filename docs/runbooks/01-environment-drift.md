# Runbook: Environment drift and reproducibility regression

## When to use

- `validate` fails due to environment mismatches (dev/staging/prod) or missing immutability signals.
- You suspect "works on my machine" problems, training/serving skew, or inconsistent inference behavior.

## Triage

1. Confirm the failing check(s) in `artifacts/report.md` and `artifacts/report.json`.
2. Identify the diverging fields (e.g., runtime version, provider versions, backend controls, missing digests).
3. Decide if drift is expected (intentional rollout) or accidental.

## Fix

- Align versions across environments (pin versions; avoid floating tags).
- Require image digests and model checksums at promotion time.
- Enforce a single source of truth for environment constraints (reviewed PRs only).

## Prevention

- Add a CI gate that runs `make lint` and blocks merges on drift-risk checks.
- Treat environment constraints as code: change via PR, review, and promotion.

