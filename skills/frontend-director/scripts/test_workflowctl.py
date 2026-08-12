#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("workflowctl.py")
PHASE_SKILLS = {
    "contract": ["define-acceptance-contract"],
    "plan": ["plan-implementation"],
    "ui": ["impeccable", "taste", "hue"],
    "ux": ["interaction-experience-design"],
    "motion": ["gsap-core"],
    "implementation": ["delivery-quality-gate"],
    "integration": ["delivery-quality-gate"],
    "security": ["delivery-quality-gate"],
}
PHASE_CHECKS = {
    "contract": ["requirements-review"],
    "plan": ["coverage-review"],
    "ui": [
        "design-direction",
        "responsive-spec",
        "state-inventory",
        "product-specificity",
        "signature-visual-plan",
    ],
    "ux": ["primary-flow-model", "failure-recovery-plan", "accessibility-plan"],
    "motion": ["motion-purpose", "reduced-motion-plan", "interruption-plan"],
    "implementation": ["tests", "typecheck", "lint", "format", "diff-review"],
    "integration": [
        "build",
        "desktop-browser",
        "mobile-browser",
        "keyboard-focus",
        "semantic-oracles",
        "reduced-motion",
        "console-clean",
        "visual-fidelity",
        "interaction-stress",
    ],
    "security": ["security-baseline", "negative-paths", "dependency-review"],
}


class WorkflowCtlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.skills_temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.skills_root = Path(self.skills_temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "app.js").write_text("export const value = 1;\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.skills_temp.cleanup()
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

    def skill_file(self, name: str) -> str:
        path = self.skills_root / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\nname: {name}\ndescription: test skill\n---\n\n# {name}\n", encoding="utf-8")
        return str(path)

    def log_skill(self, name: str) -> None:
        self.run_ctl(
            "log-skill",
            name,
            "--skill-file",
            self.skill_file(name),
            "--resources",
            "SKILL.md",
        )

    def activate_phase(self, phase: str) -> None:
        for skill in PHASE_SKILLS[phase]:
            self.log_skill(skill)
        for name in PHASE_CHECKS[phase]:
            skipped_dependency = (
                phase == "integration"
                and (
                    (name == "visual-fidelity" and self.phase_status("ui") == "skipped")
                    or (name == "interaction-stress" and self.phase_status("ux") == "skipped")
                )
            )
            args = [
                "record-gate-check",
                phase,
                "--name",
                name,
                "--kind",
                (
                    "not-applicable"
                    if skipped_dependency
                    else "automated"
                    if name in {"tests", "typecheck", "lint", "format", "build"}
                    else "manual"
                ),
                "--evidence",
                self.evidence(f"{phase}-{name}"),
                "--summary",
                (
                    f"verified {name}"
                    if not skipped_dependency
                    else f"{name} is not applicable because its design phase was skipped"
                ),
            ]
            if name in {"tests", "typecheck", "lint", "format", "build"} and not skipped_dependency:
                args.extend(["--command", f"run-{name}", "--exit-code", "0"])
            self.run_ctl(*args)

    def phase_status(self, phase: str) -> str:
        path = self.root / ".agent" / "workflow-state.json"
        if not path.is_file():
            return "pending"
        return json.loads(path.read_text(encoding="utf-8"))["phases"][phase]["status"]

    def visual_manifest(self, *, factual: bool = True, truth_mode: str = "sourced") -> str:
        screenshot_records = {}
        for rel in ("reports/desktop.png", "reports/mobile.png", "reports/detail.png"):
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = b"\x89PNG\r\n\x1a\nforward-test-image"
            path.write_bytes(payload)
            screenshot_records[Path(rel).stem] = {
                "path": rel,
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        manifest = {
            "schemaVersion": 1,
            "surface": "test product surface",
            "reviewer": {"mode": "independent-agent", "id": "reviewer-1", "blind": True},
            "signatureVisuals": [
                {
                    "id": "hero-object",
                    "role": "hero",
                    "claim": "A factual hero object",
                    "factual": factual,
                    "truthMode": truth_mode,
                    "sources": [
                        {"uri": "https://example.com/source", "license": "CC0", "note": "reference asset"}
                    ],
                    "implementationFiles": ["src/app.js"],
                    "screenshots": {
                        "desktop": screenshot_records["desktop"],
                        "mobile": screenshot_records["mobile"],
                        "detail": screenshot_records["detail"],
                    },
                    "checks": {
                        "recognizableWithoutLabel": True,
                        "entityDistinct": True,
                        "notPlaceholder": True,
                        "truthfulToClaim": True,
                        "referenceMatch": True,
                        "fullSizeCraft": True,
                    },
                    "notes": "Reviewed against the cited source at all required sizes.",
                }
            ],
            "verdict": "pass",
            "issues": [],
        }
        rel = ".agent/evidence/visual-evidence.json"
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return rel

    def pass_phase(self, phase: str) -> None:
        self.activate_phase(phase)
        self.run_ctl(
            "pass-gate",
            phase,
            "--evidence",
            self.evidence(f"{phase}-summary"),
            "--summary",
            f"{phase} pass",
        )

    def prepare_implementation(self) -> None:
        self.run_ctl("init", "--mode", "full")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "Show a value")
        self.pass_phase("contract")
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
        self.pass_phase("plan")
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
        self.pass_phase("implementation")
        self.pass_phase("integration")
        self.activate_phase("security")
        security_classification = self.evidence("security-classification")
        self.run_ctl(
            "classify-security",
            "--level",
            "low",
            "--reason",
            "Static local value with no trust boundary",
            "--evidence",
            security_classification,
        )
        self.run_ctl(
            "pass-gate",
            "security",
            "--evidence",
            self.evidence("security-summary"),
            "--summary",
            "security pass",
        )
        self.run_ctl("verify", "--finish")
        self.run_ctl("finish")
        state = json.loads((self.root / ".agent" / "workflow-state.json").read_text(encoding="utf-8"))
        self.assertEqual("done", state["status"])
        self.assertGreater(len(state["skillsUsed"]), 0)
        self.assertEqual(3, state["policyVersion"])
        self.assertEqual("Workflow complete; report verified results and residual risks.", state["nextAction"])

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
        self.pass_phase("contract")
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
        self.activate_phase("plan")
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

    def test_gate_rejects_missing_skill_activation(self) -> None:
        self.run_ctl("init")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "First")
        for name in PHASE_CHECKS["contract"]:
            self.run_ctl(
                "record-gate-check",
                "contract",
                "--name",
                name,
                "--kind",
                "manual",
                "--evidence",
                self.evidence(name),
                "--summary",
                "requirements reviewed",
            )
        failed = self.run_ctl(
            "pass-gate",
            "contract",
            "--evidence",
            self.evidence("contract-summary"),
            "--summary",
            "contract",
            expect=2,
        )
        self.assertIn("define-acceptance-contract", failed.stderr)

    def test_gate_rejects_missing_required_check(self) -> None:
        self.run_ctl("init")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "First")
        self.log_skill("define-acceptance-contract")
        failed = self.run_ctl(
            "pass-gate",
            "contract",
            "--evidence",
            self.evidence("contract-summary"),
            "--summary",
            "contract",
            expect=2,
        )
        self.assertIn("requirements-review", failed.stderr)

    def test_log_skill_requires_full_skill_instructions(self) -> None:
        self.run_ctl("init")
        failed = self.run_ctl(
            "log-skill",
            "define-acceptance-contract",
            "--skill-file",
            self.skill_file("define-acceptance-contract"),
            expect=2,
        )
        self.assertIn("SKILL.md", failed.stderr)

    def test_tampered_gate_check_cannot_pass(self) -> None:
        self.run_ctl("init")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "First")
        self.log_skill("define-acceptance-contract")
        evidence = self.evidence("requirements-review")
        self.run_ctl(
            "record-gate-check",
            "contract",
            "--name",
            "requirements-review",
            "--kind",
            "manual",
            "--evidence",
            evidence,
            "--summary",
            "requirements reviewed",
        )
        (self.root / evidence).write_text("tampered\n", encoding="utf-8")
        failed = self.run_ctl(
            "pass-gate",
            "contract",
            "--evidence",
            self.evidence("contract-summary"),
            "--summary",
            "contract",
            expect=2,
        )
        self.assertIn("requirements-review", failed.stderr)

    def test_tampered_skill_file_cannot_activate_capability(self) -> None:
        self.run_ctl("init")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "First")
        skill_path = Path(self.skill_file("define-acceptance-contract"))
        self.run_ctl(
            "log-skill",
            "define-acceptance-contract",
            "--skill-file",
            str(skill_path),
            "--resources",
            "SKILL.md",
        )
        skill_path.write_text(
            "---\nname: define-acceptance-contract\ndescription: changed\n---\n",
            encoding="utf-8",
        )
        for name in PHASE_CHECKS["contract"]:
            self.run_ctl(
                "record-gate-check",
                "contract",
                "--name",
                name,
                "--kind",
                "manual",
                "--evidence",
                self.evidence(name),
                "--summary",
                "requirements reviewed",
            )
        failed = self.run_ctl(
            "pass-gate",
            "contract",
            "--evidence",
            self.evidence("contract-summary"),
            "--summary",
            "contract",
            expect=2,
        )
        self.assertIn("loaded skill", failed.stderr)

    def test_legacy_state_requires_policy_upgrade(self) -> None:
        self.run_ctl("init")
        path = self.root / ".agent" / "workflow-state.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["schemaVersion"] = 1
        state.pop("policyVersion", None)
        path.write_text(json.dumps(state), encoding="utf-8")
        failed = self.run_ctl("verify", "--finish", expect=2)
        self.assertIn("upgrade-policy", failed.stdout)
        self.run_ctl("upgrade-policy")
        upgraded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(2, upgraded["schemaVersion"])
        self.assertEqual(3, upgraded["policyVersion"])
        self.assertEqual("active", upgraded["status"])
        self.assertEqual("contract", upgraded["currentPhase"])
        self.assertEqual("Complete and record the contract gate.", upgraded["nextAction"])

    def test_discovery_backed_fallback_can_replace_missing_skill(self) -> None:
        self.run_ctl("init")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "First")
        discovery = self.evidence("contract-skill-discovery", "define-acceptance-contract: missing\n")
        self.run_ctl(
            "log-fallback",
            "--missing-skills",
            "define-acceptance-contract",
            "--reason",
            "Host discovery returned no matching skill",
            "--reference",
            "references/contract.md",
            "--discovery-evidence",
            discovery,
        )
        for name in PHASE_CHECKS["contract"]:
            self.run_ctl(
                "record-gate-check",
                "contract",
                "--name",
                name,
                "--kind",
                "manual",
                "--evidence",
                self.evidence(name),
                "--summary",
                "requirements reviewed",
            )
        self.run_ctl(
            "pass-gate",
            "contract",
            "--evidence",
            self.evidence("contract-summary"),
            "--summary",
            "contract",
        )

    def test_high_risk_security_requires_specialist(self) -> None:
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
        self.pass_phase("implementation")
        self.pass_phase("integration")
        self.activate_phase("security")
        classification = self.evidence("security-classification")
        self.run_ctl(
            "classify-security",
            "--level",
            "high",
            "--reason",
            "Authentication and untrusted input cross a server boundary",
            "--evidence",
            classification,
        )
        failed = self.run_ctl(
            "pass-gate",
            "security",
            "--evidence",
            self.evidence("security-summary"),
            "--summary",
            "security",
            expect=2,
        )
        self.assertIn("security specialist", failed.stderr)
        self.log_skill("mantis-meta-agent")
        self.run_ctl(
            "pass-gate",
            "security",
            "--evidence",
            self.evidence("security-summary-2"),
            "--summary",
            "security",
        )

    def test_frontend_source_rejects_manual_lint_claim(self) -> None:
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
        self.log_skill("delivery-quality-gate")
        for name in PHASE_CHECKS["implementation"]:
            automated = name in {"tests", "typecheck"}
            args = [
                "record-gate-check",
                "implementation",
                "--name",
                name,
                "--kind",
                "automated" if automated else "manual",
                "--evidence",
                self.evidence(f"implementation-{name}"),
                "--summary",
                f"verified {name}",
            ]
            if automated:
                args.extend(["--command", f"run-{name}", "--exit-code", "0"])
            self.run_ctl(*args)
        failed = self.run_ctl(
            "pass-gate",
            "implementation",
            "--evidence",
            self.evidence("implementation-summary"),
            "--summary",
            "implementation",
            expect=2,
        )
        self.assertIn("automated passing lint", failed.stderr)

    def test_format_script_requires_automated_format_check(self) -> None:
        (self.root / "package.json").write_text(
            json.dumps({"scripts": {"format:check": "prettier --check ."}}), encoding="utf-8"
        )
        self.prepare_implementation()
        self.run_ctl("start-task", "T-001")
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
            self.evidence("T-001-unit"),
        )
        self.run_ctl("complete-task", "T-001", "--summary", "implemented")
        self.log_skill("delivery-quality-gate")
        for name in PHASE_CHECKS["implementation"]:
            automated = name in {"tests", "typecheck", "lint"}
            args = [
                "record-gate-check",
                "implementation",
                "--name",
                name,
                "--kind",
                "automated" if automated else "manual",
                "--evidence",
                self.evidence(f"implementation-{name}"),
                "--summary",
                f"verified {name}",
            ]
            if automated:
                args.extend(["--command", f"run-{name}", "--exit-code", "0"])
            self.run_ctl(*args)
        failed = self.run_ctl(
            "pass-gate",
            "implementation",
            "--evidence",
            self.evidence("implementation-summary"),
            "--summary",
            "implementation",
            expect=2,
        )
        self.assertIn("automated passing format", failed.stderr)

    def test_visual_manifest_rejects_fake_factual_art(self) -> None:
        manifest = self.visual_manifest(factual=True, truth_mode="intentional-abstraction")
        failed = self.run_ctl("validate-visual-evidence", "--manifest", manifest, expect=2)
        self.assertIn("cannot use 'intentional-abstraction'", failed.stderr)

    def test_visual_manifest_accepts_sourced_factual_visual(self) -> None:
        manifest = self.visual_manifest(factual=True, truth_mode="sourced")
        self.run_ctl("validate-visual-evidence", "--manifest", manifest)

    def test_visual_manifest_rejects_replaced_screenshot(self) -> None:
        manifest = self.visual_manifest(factual=True, truth_mode="sourced")
        (self.root / "reports" / "detail.png").write_bytes(b"\x89PNG\r\n\x1a\nreplaced")
        failed = self.run_ctl("validate-visual-evidence", "--manifest", manifest, expect=2)
        self.assertIn("hash does not match", failed.stderr)

    def test_filesystem_fingerprint_ignores_generated_build_metadata(self) -> None:
        spec = importlib.util.spec_from_file_location("workflowctl_under_test", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        generated = self.root / "tsconfig.tsbuildinfo"
        generated.write_text("first", encoding="utf-8")
        before = module.workspace_fingerprint(self.root)
        generated.write_text("second", encoding="utf-8")
        after = module.workspace_fingerprint(self.root)
        self.assertEqual(before, after)

    def test_latest_failed_task_check_supersedes_older_pass(self) -> None:
        self.prepare_implementation()
        self.run_ctl("start-task", "T-001")
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
            self.evidence("unit-pass"),
        )
        self.run_ctl(
            "record-check",
            "T-001",
            "--name",
            "unit",
            "--command",
            "unit-test",
            "--exit-code",
            "1",
            "--evidence",
            self.evidence("unit-fail"),
        )
        failed = self.run_ctl("complete-task", "T-001", "--summary", "implemented", expect=2)
        self.assertIn("fresh passing evidence", failed.stderr)

    def test_latest_failed_gate_check_supersedes_older_pass(self) -> None:
        self.run_ctl("init", "--mode", "full")
        self.run_ctl("add-requirement", "FR-001", "--kind", "functional", "--text", "Show a value")
        self.log_skill("define-acceptance-contract")
        self.run_ctl(
            "record-gate-check",
            "contract",
            "--name",
            "requirements-review",
            "--kind",
            "automated",
            "--command",
            "review-contract",
            "--exit-code",
            "0",
            "--evidence",
            self.evidence("contract-pass"),
            "--summary",
            "Contract requirements passed",
        )
        self.run_ctl(
            "record-gate-check",
            "contract",
            "--name",
            "requirements-review",
            "--kind",
            "automated",
            "--command",
            "review-contract",
            "--exit-code",
            "1",
            "--evidence",
            self.evidence("contract-fail"),
            "--summary",
            "Contract requirements now fail",
        )
        failed = self.run_ctl(
            "pass-gate",
            "contract",
            "--evidence",
            self.evidence("contract-summary"),
            "--summary",
            "contract pass",
            expect=2,
        )
        self.assertIn("requirements-review", failed.stderr)


if __name__ == "__main__":
    unittest.main()
