from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable

import json

from portfolio_proof.redact import redact


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass(frozen=True)
class CheckResult:
    id: str
    severity: Severity
    title: str
    passed: bool
    detail: str
    pain_point: str
    runbook: str | None = None


def _sorted_items(mapping: dict[str, Any]) -> list[tuple[str, Any]]:
    return sorted(mapping.items(), key=lambda kv: kv[0])


def _detail(value: Any) -> str:
    try:
        return json.dumps(redact(value), sort_keys=True)
    except TypeError:
        return repr(value)


def run_all_checks(config: dict[str, Any]) -> list[CheckResult]:
    envs = config["envs"]
    pipeline = config["pipeline"]
    reliability = config["reliability"]
    registry = config["registry"]

    results: list[CheckResult] = []
    results.extend(_check_environment_parity(envs, reliability))
    results.extend(_check_immutable_artifacts(pipeline, reliability, registry))
    results.extend(_check_delivery_gates_and_release(pipeline, reliability))
    results.extend(_check_oncall_readiness(reliability))
    return results


def _check_environment_parity(envs: dict[str, Any], reliability: dict[str, Any]) -> Iterable[CheckResult]:
    runbook = reliability["runbooks"]["environment_drift"]
    pain = "Reproducibility & environment drift"

    tf_versions = {name: env.get("terraform_version") for name, env in _sorted_items(envs)}
    k8s_versions = {name: env.get("kubernetes_version") for name, env in _sorted_items(envs)}

    def _all_equal(values: dict[str, Any]) -> bool:
        uniq = {v for v in values.values()}
        return len(uniq) <= 1

    passed_tf = _all_equal(tf_versions) and all(tf_versions.values())
    yield CheckResult(
        id="ENV_TERRAFORM_VERSION_PARITY",
        severity=Severity.HIGH,
        title="Terraform version is pinned and consistent across environments",
        passed=passed_tf,
        detail=_detail({"terraform_version_by_env": tf_versions}),
        pain_point=pain,
        runbook=runbook,
    )

    passed_k8s = _all_equal(k8s_versions) and all(k8s_versions.values())
    yield CheckResult(
        id="ENV_K8S_VERSION_PARITY",
        severity=Severity.HIGH,
        title="Kubernetes version is consistent across environments",
        passed=passed_k8s,
        detail=_detail({"kubernetes_version_by_env": k8s_versions}),
        pain_point=pain,
        runbook=runbook,
    )

    for env_name, env in _sorted_items(envs):
        backend = env.get("backend", {})
        passed = bool(backend.get("encryption")) and bool(backend.get("state_locking"))
        yield CheckResult(
            id=f"ENV_BACKEND_CONTROLS_{env_name.upper()}",
            severity=Severity.MEDIUM,
            title=f"{env_name}: state backend has encryption + locking enabled",
            passed=passed,
            detail=_detail({"backend": backend}),
            pain_point=pain,
            runbook=runbook,
        )


def _check_immutable_artifacts(
    pipeline: dict[str, Any], reliability: dict[str, Any], registry: dict[str, Any]
) -> Iterable[CheckResult]:
    runbook = reliability["runbooks"]["safe_release"]
    pain = "Reproducibility & artifact immutability"

    artifacts = pipeline["artifacts"]
    image_digest = artifacts.get("container_image_digest", "")
    model_checksum = artifacts.get("model_checksum", "")
    cfg_hash = artifacts.get("training_config_hash", "")
    seed = artifacts.get("random_seed")

    yield CheckResult(
        id="IMMUTABLE_IMAGE_DIGEST",
        severity=Severity.HIGH,
        title="Container image is pinned by digest",
        passed=image_digest.startswith("sha256:") and len(image_digest) > len("sha256:") + 10,
        detail=_detail({"container_image_digest": image_digest}),
        pain_point=pain,
        runbook=runbook,
    )

    yield CheckResult(
        id="IMMUTABLE_MODEL_CHECKSUM",
        severity=Severity.HIGH,
        title="Model artifact has a checksum (promotable evidence)",
        passed=model_checksum.startswith("sha256:") and len(model_checksum) > len("sha256:") + 10,
        detail=_detail({"model_checksum": model_checksum}),
        pain_point=pain,
        runbook=runbook,
    )

    yield CheckResult(
        id="IMMUTABLE_TRAINING_CONFIG_HASH",
        severity=Severity.MEDIUM,
        title="Training configuration is hashed (detects silent changes)",
        passed=cfg_hash.startswith("sha256:") and len(cfg_hash) > len("sha256:") + 10,
        detail=_detail({"training_config_hash": cfg_hash}),
        pain_point=pain,
        runbook=runbook,
    )

    yield CheckResult(
        id="DETERMINISTIC_RANDOM_SEED",
        severity=Severity.LOW,
        title="Random seed is recorded for reproducibility",
        passed=isinstance(seed, int) and seed >= 0,
        detail=_detail({"random_seed": seed}),
        pain_point=pain,
        runbook=runbook,
    )

    model_name = pipeline["pipeline"]["model_name"]
    latest = registry.get("models", {}).get(model_name, {}).get("latest_production", {})
    passed_registry = bool(latest) and latest.get("checksum") == model_checksum
    yield CheckResult(
        id="REGISTRY_MATCHES_MANIFEST",
        severity=Severity.MEDIUM,
        title="Manifest checksum matches registry latest production checksum",
        passed=passed_registry,
        detail=_detail({"registry_latest_production": latest, "manifest_model_checksum": model_checksum}),
        pain_point=pain,
        runbook=runbook,
    )


def _check_delivery_gates_and_release(pipeline: dict[str, Any], reliability: dict[str, Any]) -> Iterable[CheckResult]:
    runbook = reliability["runbooks"]["safe_release"]
    pain = "Delivery safety & CI/CD friction"

    gates = pipeline["quality_gates"]
    required_gates = [
        ("unit_tests", Severity.HIGH),
        ("integration_tests", Severity.HIGH),
        ("offline_evaluation", Severity.HIGH),
        ("security_scan_required", Severity.MEDIUM),
        ("drift_monitoring_required", Severity.MEDIUM),
        ("hallucination_mitigation_required", Severity.MEDIUM),
    ]
    for gate_key, sev in required_gates:
        yield CheckResult(
            id=f"GATE_{gate_key.upper()}",
            severity=sev,
            title=f"Quality gate required: {gate_key}",
            passed=bool(gates.get(gate_key)),
            detail=_detail({gate_key: gates.get(gate_key)}),
            pain_point=pain,
            runbook=runbook,
        )

    rel = pipeline["release"]
    yield CheckResult(
        id="RELEASE_REQUIRES_APPROVAL",
        severity=Severity.HIGH,
        title="Production promotion requires approval",
        passed=bool(rel.get("requires_approval")),
        detail=_detail({"requires_approval": rel.get("requires_approval")}),
        pain_point=pain,
        runbook=runbook,
    )

    strategy = rel.get("strategy")
    canary_percent = rel.get("canary_percent")
    passed_canary = strategy == "canary" and isinstance(canary_percent, int) and 1 <= canary_percent <= 50
    yield CheckResult(
        id="RELEASE_CANARY_POLICY",
        severity=Severity.MEDIUM,
        title="Release strategy is canary with a bounded initial traffic percentage",
        passed=passed_canary,
        detail=_detail({"strategy": strategy, "canary_percent": canary_percent}),
        pain_point=pain,
        runbook=runbook,
    )

    yield CheckResult(
        id="RELEASE_AUTO_ROLLBACK",
        severity=Severity.MEDIUM,
        title="Auto-rollback is enabled for bad releases",
        passed=bool(rel.get("auto_rollback")),
        detail=_detail({"auto_rollback": rel.get("auto_rollback")}),
        pain_point=pain,
        runbook=runbook,
    )


def _check_oncall_readiness(reliability: dict[str, Any]) -> Iterable[CheckResult]:
    pain = "Operational reliability under on-call"
    runbook = reliability["runbooks"]["ml_incident_response"]

    alerts = reliability["alerts"]
    for key in ("drift_alert", "hallucination_alert", "cost_anomaly_alert"):
        yield CheckResult(
            id=f"ALERT_{key.upper()}",
            severity=Severity.MEDIUM,
            title=f"Alerting enabled: {key}",
            passed=bool(alerts.get(key)),
            detail=_detail({key: alerts.get(key)}),
            pain_point=pain,
            runbook=runbook,
        )

    mitigations = reliability["mitigations"]
    for key in (
        "fallback_model_enabled",
        "tool_allowlist_enabled",
        "prompt_injection_filter_enabled",
        "output_safety_filter_enabled",
    ):
        yield CheckResult(
            id=f"MITIGATION_{key.upper()}",
            severity=Severity.MEDIUM,
            title=f"Mitigation in place: {key}",
            passed=bool(mitigations.get(key)),
            detail=_detail({key: mitigations.get(key)}),
            pain_point=pain,
            runbook=runbook,
        )

    runbooks = reliability.get("runbooks", {})
    yield CheckResult(
        id="RUNBOOKS_PRESENT",
        severity=Severity.HIGH,
        title="Runbooks are defined for drift, safe release, and ML incident response",
        passed=all(runbooks.get(k) for k in ("environment_drift", "safe_release", "ml_incident_response")),
        detail=_detail({"runbooks": runbooks}),
        pain_point=pain,
        runbook=runbook,
    )
