# Runbook: ML/LLM incident response (drift, hallucinations, cost spikes)

## When to use

- Drift alerts trigger (quality degradation).
- Hallucination or unsafe output reports increase.
- Cost or latency spikes exceed SLO thresholds.

## Immediate actions

1. **Stabilize**: reduce traffic to the affected model, enable a fallback, or roll back.
2. **Limit blast radius**: tighten tool access (agent/tool usage), apply rate limits, and disable risky features.
3. **Capture evidence**: snapshot the manifest (versions, digests, config hashes), and sample affected requests/responses.

## Diagnosis

- Check feature distribution shifts (input data drift).
- Validate prompt templates and retrieval configuration (RAG index version).
- Review latency/cost breakdown by route and tool calls.

## Follow-ups

- Add missing monitors and alerts.
- Improve evaluation coverage for the failure mode.
- Update runbooks and promotion gates to prevent recurrence.

