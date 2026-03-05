from __future__ import annotations

import argparse
import sys

from portfolio_proof.commands import cmd_report, cmd_validate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="portfolio_proof",
        description="Deterministic ML delivery guardrails: reproducibility, safe releases, and incident readiness.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    report_p = sub.add_parser("report", help="Generate a human-readable report under artifacts/.")
    report_p.add_argument("--examples", default="examples", help="Path to examples/ directory.")
    report_p.add_argument("--out", default="artifacts/report.md", help="Output markdown path.")
    report_p.set_defaults(_fn=cmd_report)

    val_p = sub.add_parser("validate", help="Validate example inputs; exit non-zero on violations.")
    val_p.add_argument("--examples", default="examples", help="Path to examples/ directory.")
    val_p.set_defaults(_fn=cmd_validate)

    args = parser.parse_args(argv)
    return int(args._fn(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

