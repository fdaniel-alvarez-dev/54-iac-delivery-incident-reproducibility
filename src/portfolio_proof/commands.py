from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from portfolio_proof.checks import Severity, run_all_checks
from portfolio_proof.config import load_all
from portfolio_proof.report import render_markdown_report


def cmd_report(args: Any) -> int:
    cfg = load_all(Path(args.examples))
    results = run_all_checks(cfg)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    md = render_markdown_report(results, cfg)
    out_path.write_text(md, encoding="utf-8")

    json_path = out_path.with_suffix(".json")
    payload = {
        "tool": "portfolio_proof",
        "cwd": os.getcwd(),
        "examples_path": str(Path(args.examples)),
        "results": [asdict(r) for r in results],
    }
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return 0


def cmd_validate(args: Any) -> int:
    cfg = load_all(Path(args.examples))
    results = run_all_checks(cfg)

    failures = [r for r in results if not r.passed and r.severity in (Severity.HIGH, Severity.MEDIUM)]
    if failures:
        for r in sorted(failures, key=lambda x: (x.severity.value, x.id)):
            print(f"FAIL [{r.severity.value}] {r.id}: {r.title}", file=sys.stderr)
        return 2
    return 0
