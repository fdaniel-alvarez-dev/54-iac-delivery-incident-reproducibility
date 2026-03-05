# Runbook: Safe ML/LLM release (promotion + rollback)

## When to use

- You are promoting a model/LLM workflow to production.
- You need to reduce release risk (latency/accuracy/cost regressions).

## Release checklist (minimum)

1. Quality gates pass: tests, offline evaluation, and basic safety checks.
2. Promotion requires approval for production.
3. Rollback is defined and executable (previous model version + config).
4. Canary plan is defined (traffic %, evaluation window, stop conditions).

## If something goes wrong

- Stop the rollout (set canary to 0% / pause deployment).
- Roll back to the previously known-good model version.
- Document a blameless incident timeline and action items.

