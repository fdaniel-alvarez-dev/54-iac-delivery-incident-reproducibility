from __future__ import annotations

from pathlib import Path
from typing import Any

import tomllib

from portfolio_proof.registry import load_registry


class ConfigError(ValueError):
    pass


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing required file: {path}")
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"Invalid TOML root in {path}")
    return data


def load_all(examples_dir: Path) -> dict[str, Any]:
    examples_dir = examples_dir.resolve()

    envs_toml = _load_toml(examples_dir / "iac_envs.toml")
    pipeline_toml = _load_toml(examples_dir / "ml_pipeline.toml")
    reliability_toml = _load_toml(examples_dir / "reliability.toml")

    envs = envs_toml.get("env", {})
    if not isinstance(envs, dict) or not envs:
        raise ConfigError("iac_envs.toml must contain [env.<name>] sections.")

    pipeline = pipeline_toml
    for key in ("pipeline", "artifacts", "quality_gates", "release", "registry"):
        if key not in pipeline:
            raise ConfigError(f"ml_pipeline.toml missing required section: [{key}]")

    reliability = reliability_toml
    for key in ("slo", "alerts", "mitigations", "runbooks"):
        if key not in reliability:
            raise ConfigError(f"reliability.toml missing required section: [{key}]")

    registry_cfg = pipeline["registry"]
    registry = load_registry(registry_cfg, examples_dir)

    return {
        "envs": envs,
        "pipeline": pipeline,
        "reliability": reliability,
        "registry": registry,
    }
