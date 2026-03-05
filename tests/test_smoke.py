from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class SmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="portfolio-proof-"))
        self.artifacts = self.tmpdir / "artifacts"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "portfolio_proof", *args],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validate_passes_on_examples(self) -> None:
        proc = self._run("validate", "--examples", "examples")
        self.assertEqual(proc.returncode, 0, msg=f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")

    def test_report_generates_markdown(self) -> None:
        out = self.artifacts / "report.md"
        proc = self._run("report", "--examples", "examples", "--out", str(out))
        self.assertEqual(proc.returncode, 0, msg=f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        self.assertTrue(out.exists(), "report.md not created")
        content = out.read_text(encoding="utf-8")
        self.assertIn("# Portfolio Proof Report", content)
        self.assertIn("## Results (mapped to pain points)", content)

