#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("evaluate_runs.py")


class EvaluateRunsTests(unittest.TestCase):
    def test_matched_pair_reports_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = {
                "schemaVersion": 1,
                "agent": "opencode",
                "model": "deepseek",
                "taskId": "form",
                "seed": 1,
            }
            control = {
                **base,
                "runId": "control-1",
                "variant": "control",
                "metrics": {"codeQuality": 60, "criticalRegressions": 2, "tokens": 1000},
            }
            skill = {
                **base,
                "runId": "skill-1",
                "variant": "skill",
                "metrics": {"codeQuality": 80, "criticalRegressions": 0, "tokens": 1200},
            }
            (root / "control.json").write_text(json.dumps(control), encoding="utf-8")
            (root / "skill.json").write_text(json.dumps(skill), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(root), "--format", "json"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(1, report["matchedPairs"])
            self.assertEqual(20, report["aggregateDeltas"]["codeQuality"])
            self.assertEqual(2, report["aggregateDeltas"]["criticalRegressions"])
            self.assertEqual(-200, report["aggregateDeltas"]["tokens"])

    def test_unmatched_run_cannot_claim_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "skill.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "runId": "skill-1",
                        "variant": "skill",
                        "agent": "hermes",
                        "model": "deepseek",
                        "taskId": "form",
                        "seed": 1,
                        "metrics": {"codeQuality": 80},
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(1, completed.returncode)
            self.assertIn("no quality claim", completed.stdout)


if __name__ == "__main__":
    unittest.main()
