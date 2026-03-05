from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class RegistryError(ValueError):
    pass


def load_registry(registry_cfg: dict[str, Any], examples_dir: Path) -> dict[str, Any]:
    reg_type = registry_cfg.get("type")
    if reg_type == "mock":
        reg_path = registry_cfg.get("path")
        if not reg_path:
            raise RegistryError("ml_pipeline.toml [registry] type=mock requires path=...")
        path = (examples_dir / str(reg_path)).resolve()
        return _load_json(path)

    if reg_type == "http":
        url = registry_cfg.get("url")
        if not url:
            raise RegistryError("ml_pipeline.toml [registry] type=http requires url=...")
        headers = _auth_headers(registry_cfg)
        return _http_get_json(str(url), headers=headers)

    if reg_type == "mlflow":
        url = registry_cfg.get("url")
        model_name = registry_cfg.get("model_name")
        if not url or not model_name:
            raise RegistryError("ml_pipeline.toml [registry] type=mlflow requires url=... and model_name=...")
        headers = _auth_headers(registry_cfg)
        return _mlflow_registry_snapshot(str(url), str(model_name), headers=headers)

    raise RegistryError(f"Unsupported registry.type={reg_type!r}. Supported: mock, http, mlflow.")


def _auth_headers(registry_cfg: dict[str, Any]) -> dict[str, str]:
    token_env = registry_cfg.get("bearer_token_env")
    if not token_env:
        return {}
    token = os.environ.get(str(token_env), "")
    if not token:
        raise RegistryError(f"Missing bearer token env var: {token_env}")
    return {"Authorization": f"Bearer {token}"}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise RegistryError(f"Missing required file: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RegistryError(f"Invalid JSON root in {path}")
    return data


def _http_get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=dict(headers))
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = resp.read().decode("utf-8")
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise RegistryError("HTTP registry response must be a JSON object")
    return data


def _mlflow_registry_snapshot(base_url: str, model_name: str, headers: dict[str, str]) -> dict[str, Any]:
    """
    Produces a normalized snapshot compatible with the demo schema:
      {"models": {<name>: {"latest_production": {"version": "...", "checksum": "sha256:..."}}}}

    The checksum is read from the MLflow model version tag `model_checksum` if present.
    """
    base = base_url.rstrip("/")
    version = _mlflow_get_latest_production_version(base, model_name, headers=headers)
    checksum = _mlflow_get_model_version_checksum(base, model_name, version, headers=headers)
    return {
        "models": {
            model_name: {
                "latest_production": {
                    "version": version,
                    "checksum": checksum,
                }
            }
        }
    }


def _mlflow_get_latest_production_version(base: str, model_name: str, headers: dict[str, str]) -> str:
    url = f"{base}/api/2.0/mlflow/registered-models/get-latest-versions"
    body = json.dumps({"name": model_name, "stages": ["Production"]}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **headers}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = resp.read().decode("utf-8")
    data = json.loads(payload)
    versions = data.get("model_versions") or []
    if not versions:
        raise RegistryError(f"MLflow returned no Production versions for {model_name!r}")
    version = versions[0].get("version")
    if not version:
        raise RegistryError("MLflow response missing model_versions[0].version")
    return str(version)


def _mlflow_get_model_version_checksum(
    base: str, model_name: str, version: str, headers: dict[str, str]
) -> str:
    qs = urllib.parse.urlencode({"name": model_name, "version": version})
    url = f"{base}/api/2.0/mlflow/model-versions/get?{qs}"
    req = urllib.request.Request(url, headers=dict(headers))
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = resp.read().decode("utf-8")
    data = json.loads(payload)
    mv = data.get("model_version") or {}
    tags = mv.get("tags") or []
    for t in tags:
        if t.get("key") == "model_checksum" and t.get("value"):
            return str(t["value"])
    return ""

