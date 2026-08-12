#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("workflowctl.py")


class WorkflowCtlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "app.js").write_text("export const value = 1;\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_ctl(self, *args: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(expect, completed.returncode, completed.stdout + completed.stderr)
        return completed

    def evidence(self, name: str, content: str = "pass\n") -> str:
        rel = f".agent/evidence/{name}.txt"
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return rel

    def prepare_implementation(self) -> None:
        self.run_ctl("init", "--mode", "full")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "Show a value")
        self.run_ctl("pass-gate", "contract", "--evidence", self.evidence("contract"), "--summary", "contract")
        self.run_ctl(
            "add-task",
            "T-001",
            "--title",
            "Implement value",
            "--requirements",
            "FR-001",
            "--files",
            "src/app.js",
            "--checks",
            "unit",
        )
        self.run_ctl("pass-gate", "plan", "--evidence", self.evidence("plan"), "--summary", "plan")
        self.run_ctl("skip-phase", "ui", "--reason", "No visual change")
        self.run_ctl("skip-phase", "ux", "--reason", "No interaction change")
        self.run_ctl("skip-phase", "motion", "--reason", "No motion")

    def test_full_happy_path(self) -> None:
        self.prepare_implementation()
        self.run_ctl("start-task", "T-001")
        check = self.evidence("T-001-unit")
        self.run_ctl(
            "record-check",
            "T-001",
            "--name",
            "unit",
            "--command",
            "unit-test",
            "--exit-code",
            "0",
            "--evidence",
            check,
        )
        self.run_ctl("complete-task", "T-001", "--summary", "implemented")
        self.run_ctl("pass-gate", "implementation", "--evidence", check, "--summary", "tasks complete")
        integration = self.evidence("integration")
        self.run_ctl("pass-gate", "integration", "--evidence", integration, "--summary", "integration pass")
        security = self.evidence("security")
        self.run_ctl("pass-gate", "security", "--evidence", security, "--summary", "security pass")
        self.run_ctl("verify", "--finish")
        self.run_ctl("finish")
        state = json.loads((self.root / ".agent" / "workflow-state.json").read_text(encoding="utf-8"))
        self.assertEqual("done", state["status"])

    def test_source_change_makes_task_check_stale(self) -> None:
        self.prepare_implementation()
        self.run_ctl("start-task", "T-001")
        check = self.evidence("T-001-unit")
        self.run_ctl(
            "record-check",
            "T-001",
            "--name",
            "unit",
            "--command",
            "unit-test",
            "--exit-code",
            "0",
            "--evidence",
            check,
        )
        (self.root / "src" / "app.js").write_text("export const value = 2;\n", encoding="utf-8")
        failed = self.run_ctl("complete-task", "T-001", "--summary", "implemented", expect=2)
        self.assertIn("fresh passing evidence", failed.stderr)

    def test_evidence_tampering_makes_check_stale(self) -> None:
        self.prepare_implementation()
        self.run_ctl("start-task", "T-001")
        check = self.evidence("T-001-unit")
        self.run_ctl(
            "record-check",
            "T-001",
            "--name",
            "unit",
            "--command",
            "unit-test",
            "--exit-code",
            "0",
            "--evidence",
            check,
        )
        (self.root / check).write_text("rewritten\n", encoding="utf-8")
        failed = self.run_ctl("complete-task", "T-001", "--summary", "implemented", expect=2)
        self.assertIn("fresh passing evidence", failed.stderr)

    def test_plan_gate_rejects_uncovered_requirement(self) -> None:
        self.run_ctl("init")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "First")
        self.run_ctl("add-requirement", "FR-002", "--kind", "functional", "--text", "Second")
        self.run_ctl("pass-gate", "contract", "--evidence", self.evidence("contract"), "--summary", "contract")
        self.run_ctl(
            "add-task",
            "T-001",
            "--title",
            "Only first",
            "--requirements",
            "FR-001",
            "--files",
            "src/app.js",
        )
        failed = self.run_ctl(
            "pass-gate",
            "plan",
            "--evidence",
            self.evidence("plan"),
            "--summary",
            "plan",
            expect=2,
        )
        self.assertIn("FR-002", failed.stderr)


if __name__ == "__main__":
    unittest.main()
