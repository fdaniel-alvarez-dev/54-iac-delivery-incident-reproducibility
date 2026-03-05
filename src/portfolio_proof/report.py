from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from portfolio_proof.checks import CheckResult, Severity


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def render_markdown_report(results: list[CheckResult], config: dict[str, Any]) -> str:
    by_pain: dict[str, list[CheckResult]] = defaultdict(list)
    for r in sorted(results, key=lambda x: (x.pain_point, x.severity.value, x.id)):
        by_pain[r.pain_point].append(r)

    failures = [r for r in results if not r.passed]
    fail_high = sum(1 for r in failures if r.severity == Severity.HIGH)
    fail_med = sum(1 for r in failures if r.severity == Severity.MEDIUM)
    fail_low = sum(1 for r in failures if r.severity == Severity.LOW)

    pipeline = config["pipeline"]["pipeline"]
    model_name = pipeline.get("model_name", "unknown")
    pipeline_name = pipeline.get("name", "unknown")

    lines: list[str] = []
    lines.append("# Portfolio Proof Report")
    lines.append("")
    lines.append(f"- Generated (UTC): `{_now_utc_iso()}`")
    lines.append(f"- Pipeline: `{pipeline_name}`")
    lines.append(f"- Model: `{model_name}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total checks: **{len(results)}**")
    lines.append(f"- Failures: **{len(failures)}** (HIGH={fail_high}, MEDIUM={fail_med}, LOW={fail_low})")
    lines.append("")
    lines.append("## Results (mapped to pain points)")
    lines.append("")

    for pain_point in sorted(by_pain.keys()):
        lines.append(f"### {pain_point}")
        lines.append("")
        for r in by_pain[pain_point]:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"- **{status}** [{r.severity.value}] `{r.id}` — {r.title}")
            lines.append(f"  - Detail: {r.detail}")
            if r.runbook:
                lines.append(f"  - Runbook: `{r.runbook}`")
        lines.append("")

    lines.append("## Recommended guardrails")
    lines.append("")
    lines.extend(_recommendations(results, config))
    lines.append("")
    lines.append("## Validation")
    lines.append("")
    lines.append("`validate` exits non-zero if any HIGH/MEDIUM checks fail.")
    lines.append("")
    return "\n".join(lines)


def _recommendations(results: list[CheckResult], config: dict[str, Any]) -> list[str]:
    failed_ids = {r.id for r in results if not r.passed}
    recs: list[str] = []

    if "IMMUTABLE_IMAGE_DIGEST" in failed_ids:
        recs.append("- Pin container images by digest (no floating tags) and enforce in CI.")
    if "IMMUTABLE_MODEL_CHECKSUM" in failed_ids:
        recs.append("- Require model artifact checksums at promotion time; store as deploy-time evidence.")
    if "ENV_TERRAFORM_VERSION_PARITY" in failed_ids or "ENV_K8S_VERSION_PARITY" in failed_ids:
        recs.append("- Enforce environment parity (versions + backend controls) to avoid training/serving skew.")

    rel = config["pipeline"]["release"]
    if not rel.get("requires_approval"):
        recs.append("- Require explicit approval for production promotions to reduce release risk.")
    if rel.get("strategy") != "canary":
        recs.append("- Adopt canary releases for ML/LLM changes; define stop conditions and rollback plan.")

    if not recs:
        recs.append("- Current example inputs pass; use these configs as a baseline and extend for your org.")
    return recs

