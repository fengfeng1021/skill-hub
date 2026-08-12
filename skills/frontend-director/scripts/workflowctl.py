#!/usr/bin/env python3
"""Portable state controller for the frontend-director Agent Skill.

Uses only the Python standard library. It records workflow structure and evidence;
it deliberately does not execute project test commands on behalf of the agent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Optional


SCHEMA_VERSION = 2
SKILL_VERSION = "6.0.0"
POLICY_VERSION = 2
WORKFLOW = "frontend-director"
STATE_REL = Path(".agent") / "workflow-state.json"
PHASES = (
    "contract",
    "plan",
    "ui",
    "ux",
    "motion",
    "implementation",
    "integration",
    "security",
)
OPTIONAL_PHASES = {"ui", "ux", "motion"}
REQUIRED_PHASES = set(PHASES) - OPTIONAL_PHASES
SEVERITIES = {"critical", "high", "medium", "low"}
CHECK_KINDS = {"automated", "manual", "not-applicable"}

# Every passed phase must prove that its specialist capability was actually
# loaded. A portable built-in fallback is allowed only when discovery evidence
# shows that the external skill is unavailable.
PHASE_SKILL_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "contract": (("define-acceptance-contract",),),
    "plan": (("plan-implementation",),),
    "ui": (("impeccable",), ("taste",), ("hue",)),
    "ux": (("interaction-experience-design",),),
    "motion": (("gsap-core", "gsap-timeline", "gsap-scrolltrigger", "gsap-react", "gsap-frameworks"),),
    "implementation": (("delivery-quality-gate",),),
    "integration": (("delivery-quality-gate",),),
    "security": (("delivery-quality-gate",),),
}
PHASE_FALLBACK_REFERENCES = {
    "contract": "references/contract.md",
    "plan": "references/implementation-plan.md",
    "ui": "references/ui-quality.md",
    "ux": "references/ux-interaction.md",
    "motion": "references/motion.md",
    "implementation": "references/coding-loop.md",
    "integration": "references/verification.md",
    "security": "references/security.md",
}
PHASE_REQUIRED_CHECKS: dict[str, tuple[str, ...]] = {
    "contract": ("requirements-review",),
    "plan": ("coverage-review",),
    "ui": ("design-direction", "responsive-spec", "state-inventory", "product-specificity"),
    "ux": ("primary-flow-model", "failure-recovery-plan", "accessibility-plan"),
    "motion": ("motion-purpose", "reduced-motion-plan", "interruption-plan"),
    "implementation": ("tests", "typecheck", "lint", "diff-review"),
    "integration": (
        "build",
        "desktop-browser",
        "mobile-browser",
        "keyboard-focus",
        "semantic-oracles",
        "reduced-motion",
        "console-clean",
    ),
    "security": ("security-baseline", "negative-paths", "dependency-review"),
}
SECURITY_SPECIALIST_MARKERS = ("mantis", "security", "threat")
PROJECT_SCAN_EXCLUDES = {".git", ".agent", "node_modules", "dist", "build", ".next", "coverage"}
FRONTEND_CODE_SUFFIXES = {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte"}
TYPED_FRONTEND_SUFFIXES = {".ts", ".tsx", ".vue", ".svelte"}


class WorkflowError(RuntimeError):
    """User-correctable workflow error."""


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_rel(value: str) -> str:
    raw = value.strip().replace("\\", "/")
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or ".." in path.parts:
        raise WorkflowError(f"Path must stay inside the project: {value!r}")
    return str(path)


def split_csv(values: Optional[Iterable[str]]) -> list[str]:
    result: list[str] = []
    for value in values or []:
        for part in value.split(","):
            item = part.strip()
            if item and item not in result:
                result.append(item)
    return result


def resolve_project_path(root: Path, relative: str) -> Path:
    normalized = normalize_rel(relative)
    target = (root / Path(normalized)).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise WorkflowError(f"Path escapes project root: {relative!r}") from exc
    return target


def run_git(root: Path, args: list[str]) -> Optional[bytes]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return None
    return completed.stdout if completed.returncode == 0 else None


def workspace_fingerprint(root: Path) -> str:
    """Hash source state while excluding controller artifacts and heavy build output."""
    digest = hashlib.sha256()
    head = run_git(root, ["rev-parse", "HEAD"])
    if head is not None:
        digest.update(head.strip())
        pathspec = ["--", ".", ":(exclude).agent/**"]
        for args in (
            ["diff", "--no-ext-diff", "--binary", *pathspec],
            ["diff", "--no-ext-diff", "--binary", "--cached", *pathspec],
        ):
            digest.update(run_git(root, args) or b"")
        untracked = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"]) or b""
        for raw in sorted(filter(None, untracked.split(b"\0"))):
            rel = raw.decode("utf-8", errors="surrogateescape").replace("\\", "/")
            if rel == ".agent" or rel.startswith(".agent/"):
                continue
            digest.update(raw)
            file_path = root / Path(rel)
            if file_path.is_file():
                try:
                    digest.update(file_path.read_bytes())
                except OSError:
                    digest.update(b"<unreadable>")
        return f"git:{digest.hexdigest()}"

    excluded = {".git", ".agent", "node_modules", "dist", "build", ".next", "coverage"}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not excluded.intersection(p.relative_to(root).parts)):
        rel = path.relative_to(root).as_posix()
        try:
            stat = path.stat()
            digest.update(f"{rel}\0{stat.st_size}\0{stat.st_mtime_ns}\n".encode("utf-8"))
        except OSError:
            digest.update(f"{rel}\0<unreadable>\n".encode("utf-8"))
    return f"fs:{digest.hexdigest()}"


def scope_fingerprint(root: Path, files: list[str]) -> str:
    if not files:
        return workspace_fingerprint(root)
    digest = hashlib.sha256()
    for rel in sorted(files):
        path = resolve_project_path(root, rel)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        if not path.exists():
            digest.update(b"<missing>")
        elif path.is_file():
            try:
                digest.update(path.read_bytes())
            except OSError:
                digest.update(b"<unreadable>")
        else:
            digest.update(b"<not-file>")
        digest.update(b"\n")
    return f"scope:{digest.hexdigest()}"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise WorkflowError(f"Cannot hash evidence file {path}: {exc}") from exc
    return digest.hexdigest()


def skill_frontmatter_name(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkflowError(f"Cannot read skill file {path}: {exc}") from exc
    match = re.match(r"^---\s*\n(?P<header>.*?)\n---(?:\s*\n|$)", text, flags=re.DOTALL)
    if not match:
        raise WorkflowError(f"Skill file has no YAML frontmatter: {path}")
    name = re.search(r"^name:\s*['\"]?(?P<name>[^'\"\n]+?)['\"]?\s*$", match.group("header"), flags=re.MULTILINE)
    if not name:
        raise WorkflowError(f"Skill file frontmatter has no name: {path}")
    return name.group("name").strip()


def skill_activation_valid(entry: dict[str, Any]) -> bool:
    skill_file = entry.get("skillFile")
    expected = entry.get("skillFileSha256")
    if not skill_file or not expected:
        return False
    path = Path(skill_file)
    return path.is_absolute() and path.is_file() and file_sha256(path) == expected


def uses_enforced_policy(state: dict[str, Any]) -> bool:
    return int(state.get("policyVersion", 1)) >= POLICY_VERSION


def evidence_integrity_ok(root: Path, record: dict[str, Any], *, require_current_workspace: bool) -> bool:
    evidence = record.get("evidence")
    if not evidence:
        return False
    evidence_path = resolve_project_path(root, evidence)
    if not evidence_path.is_file() or record.get("evidenceSha256") != file_sha256(evidence_path):
        return False
    if require_current_workspace and record.get("workspaceFingerprint") != workspace_fingerprint(root):
        return False
    return True


def phase_capability_errors(
    root: Path,
    state: dict[str, Any],
    phase: str,
    *,
    require_current_workspace: bool,
) -> list[str]:
    if not uses_enforced_policy(state):
        return []
    loaded = {
        entry.get("name")
        for entry in state.get("skillsUsed", [])
        if entry.get("phase") == phase
        and entry.get("valid", True)
        and "SKILL.md" in entry.get("resources", [])
        and skill_activation_valid(entry)
    }
    fallbacks = [
        entry
        for entry in state.get("capabilityFallbacks", [])
        if entry.get("phase") == phase and entry.get("valid", True)
    ]
    errors: list[str] = []
    for group in PHASE_SKILL_GROUPS[phase]:
        if loaded.intersection(group):
            continue
        covered = any(
            set(entry.get("missingSkills", [])).intersection(group)
            and entry.get("reference") == PHASE_FALLBACK_REFERENCES[phase]
            and evidence_integrity_ok(root, entry, require_current_workspace=require_current_workspace)
            for entry in fallbacks
        )
        if not covered:
            errors.append(
                f"{phase} gate requires a loaded skill from ({', '.join(group)}) "
                "or a discovery-backed fallback"
            )
    return errors


def phase_check_errors(
    root: Path,
    state: dict[str, Any],
    phase: str,
    *,
    require_current_workspace: bool,
) -> list[str]:
    if not uses_enforced_policy(state):
        return []
    phase_state = state.get("phases", {}).get(phase, {})
    valid_names: set[str] = set()
    errors: list[str] = []
    for check in phase_state.get("checks", []):
        if not check.get("valid"):
            continue
        if check.get("kind") == "automated" and check.get("exitCode") != 0:
            continue
        if evidence_integrity_ok(root, check, require_current_workspace=require_current_workspace):
            valid_names.add(str(check.get("name")))
    for name in PHASE_REQUIRED_CHECKS[phase]:
        if name not in valid_names:
            errors.append(f"{phase} gate requires fresh check evidence: {name}")
    return errors


def phase_summary_evidence_errors(root: Path, state: dict[str, Any], phase: str) -> list[str]:
    if not uses_enforced_policy(state):
        return []
    phase_state = state.get("phases", {}).get(phase, {})
    evidence = phase_state.get("evidence", [])
    if len(evidence) != 1:
        return [f"{phase} gate must have exactly one summary evidence file"]
    record = {
        "evidence": evidence[0],
        "evidenceSha256": phase_state.get("evidenceSha256"),
        "workspaceFingerprint": phase_state.get("workspaceFingerprint"),
    }
    require_current = phase in {"implementation", "integration", "security"}
    if not evidence_integrity_ok(root, record, require_current_workspace=require_current):
        return [f"{phase} gate summary evidence is missing, tampered, or stale"]
    return []


def project_source_suffixes(root: Path) -> set[str]:
    suffixes: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file() or PROJECT_SCAN_EXCLUDES.intersection(path.relative_to(root).parts):
            continue
        if path.suffix.lower() in FRONTEND_CODE_SUFFIXES:
            suffixes.add(path.suffix.lower())
    return suffixes


def project_tooling_errors(root: Path, state: dict[str, Any], phase: str) -> list[str]:
    if not uses_enforced_policy(state) or phase not in {"implementation", "integration"}:
        return []
    suffixes = project_source_suffixes(root)
    if not suffixes:
        return []
    valid_automated = {
        check.get("name")
        for check in state.get("phases", {}).get(phase, {}).get("checks", [])
        if check.get("valid")
        and check.get("kind") == "automated"
        and check.get("exitCode") == 0
        and evidence_integrity_ok(root, check, require_current_workspace=True)
    }
    errors: list[str] = []
    if phase == "implementation":
        for name in ("tests", "lint"):
            if name not in valid_automated:
                errors.append(f"Frontend source requires an automated passing {name} check")
        if suffixes.intersection(TYPED_FRONTEND_SUFFIXES) and "typecheck" not in valid_automated:
            errors.append("Typed frontend source requires an automated passing typecheck check")
    if phase == "integration" and "build" not in valid_automated:
        errors.append("Frontend source requires an automated passing build check")
    return errors


def security_classification_errors(root: Path, state: dict[str, Any]) -> list[str]:
    if not uses_enforced_policy(state):
        return []
    classification = state.get("securityClassification")
    if not isinstance(classification, dict):
        return ["Security gate requires an explicit low/medium/high classification"]
    errors: list[str] = []
    if not evidence_integrity_ok(root, classification, require_current_workspace=True):
        errors.append("Security classification evidence is missing, tampered, or stale")
    if classification.get("level") == "high":
        specialist_loaded = any(
            entry.get("phase") == "security"
            and entry.get("valid", True)
            and skill_activation_valid(entry)
            and entry.get("name") != "delivery-quality-gate"
            and any(marker in str(entry.get("name", "")).lower() for marker in SECURITY_SPECIALIST_MARKERS)
            for entry in state.get("skillsUsed", [])
        )
        if not specialist_loaded:
            errors.append("High-risk security delivery requires a loaded Mantis or equivalent security specialist")
    return errors


def state_path(root: Path) -> Path:
    return root / STATE_REL


def load_state(root: Path) -> dict[str, Any]:
    path = state_path(root)
    if not path.is_file():
        raise WorkflowError(f"Workflow state not found: {path}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkflowError(f"Cannot read workflow state: {exc}") from exc
    if state.get("schemaVersion") not in {1, SCHEMA_VERSION} or state.get("workflow") != WORKFLOW:
        raise WorkflowError("Unsupported or unrelated workflow-state.json")
    # Keep v5 runs readable and resumable. New enforcement applies only to
    # states initialized with policyVersion 2.
    state.setdefault("policyVersion", 1)
    state.setdefault("capabilityFallbacks", [])
    state.setdefault("securityClassification", None)
    for phase in PHASES:
        state.setdefault("phases", {}).setdefault(phase, {}).setdefault("checks", [])
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updatedAt"] = now()
    encoded = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    handle, temp_name = tempfile.mkstemp(prefix="workflow-state-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def audit(state: dict[str, Any], event: str, **details: Any) -> None:
    entry = {"at": now(), "event": event}
    entry.update({key: value for key, value in details.items() if value not in (None, [], "")})
    state.setdefault("audit", []).append(entry)


def set_next_action(state: dict[str, Any]) -> None:
    if state.get("status") == "done":
        state["nextAction"] = "Workflow complete; report verified results and residual risks."
        return
    if all(state.get("phases", {}).get(phase, {}).get("status") in {"passed", "skipped"} for phase in PHASES):
        state["nextAction"] = "Run verify --finish, then finish the workflow."
        return
    current_task = state.get("currentTask")
    if current_task:
        state["nextAction"] = f"Complete the Coding Loop for {current_task}."
        return
    phase = state.get("currentPhase")
    if phase == "implementation":
        pending = [tid for tid, task in state.get("tasks", {}).items() if task.get("status") != "completed"]
        state["nextAction"] = f"Start the next implementation task: {pending[0]}." if pending else "Pass the implementation gate."
    else:
        state["nextAction"] = f"Complete and record the {phase} gate."


def phase_index(phase: str) -> int:
    try:
        return PHASES.index(phase)
    except ValueError as exc:
        raise WorkflowError(f"Unknown phase: {phase}") from exc


def advance_after_gate(state: dict[str, Any], phase: str) -> None:
    index = phase_index(phase)
    if index + 1 < len(PHASES):
        next_phase = PHASES[index + 1]
        state["currentPhase"] = next_phase
        if state["phases"][next_phase]["status"] in {"pending", "invalid"}:
            state["phases"][next_phase]["status"] = "in_progress"
    else:
        state["currentPhase"] = "security"
    set_next_action(state)


def fresh_passing_checks(root: Path, task: dict[str, Any]) -> list[dict[str, Any]]:
    current = scope_fingerprint(root, task.get("files", []))
    fresh: list[dict[str, Any]] = []
    valid_checks = [check for check in task.get("checks", []) if check.get("valid") and check.get("exitCode") == 0]
    for check in valid_checks:
        evidence = check.get("evidence")
        if not evidence:
            continue
        evidence_path = resolve_project_path(root, evidence)
        if (
            evidence_path.is_file()
            and check.get("scopeFingerprint") == current
            and check.get("evidenceSha256") == file_sha256(evidence_path)
        ):
            fresh.append(check)
    return fresh


def task_fresh(root: Path, task: dict[str, Any]) -> bool:
    checks = fresh_passing_checks(root, task)
    if not checks:
        return False
    expected = set(task.get("expectedChecks", []))
    return expected.issubset({check.get("name") for check in checks})


def coverage_errors(state: dict[str, Any]) -> list[str]:
    requirements = set(state.get("requirements", {}))
    covered: set[str] = set()
    errors: list[str] = []
    for task_id, task in state.get("tasks", {}).items():
        task_requirements = set(task.get("requirements", []))
        unknown = task_requirements - requirements
        if unknown:
            errors.append(f"{task_id} references unknown requirements: {', '.join(sorted(unknown))}")
        covered.update(task_requirements)
        if not task.get("files"):
            errors.append(f"{task_id} has no declared file scope")
        dependencies = task.get("dependsOn", [])
        if task_id in dependencies:
            errors.append(f"{task_id} cannot depend on itself")
        unknown_dependencies = set(dependencies) - set(state.get("tasks", {}))
        if unknown_dependencies:
            errors.append(f"{task_id} has unknown dependencies: {', '.join(sorted(unknown_dependencies))}")
    for requirement in sorted(requirements - covered):
        errors.append(f"Requirement is not covered by any task: {requirement}")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(task_id: str, trail: list[str]) -> None:
        if task_id in visiting:
            errors.append(f"Task dependency cycle: {' -> '.join([*trail, task_id])}")
            return
        if task_id in visited or task_id not in state.get("tasks", {}):
            return
        visiting.add(task_id)
        for dependency in state["tasks"][task_id].get("dependsOn", []):
            visit(dependency, [*trail, task_id])
        visiting.remove(task_id)
        visited.add(task_id)

    for task_id in state.get("tasks", {}):
        visit(task_id, [])
    return errors


def validate_state(root: Path, state: dict[str, Any], *, for_finish: bool = False) -> list[str]:
    errors: list[str] = []
    if state.get("currentPhase") not in PHASES:
        errors.append("currentPhase is invalid")
    if state.get("currentTask") and state["currentTask"] not in state.get("tasks", {}):
        errors.append("currentTask does not exist")
    errors.extend(coverage_errors(state))

    for task_id, task in state.get("tasks", {}).items():
        if task.get("status") == "completed" and not task_fresh(root, task):
            errors.append(f"{task_id} is completed but has no fresh passing evidence")

    if not for_finish:
        return errors

    if not uses_enforced_policy(state):
        errors.append("Legacy workflow policy cannot finish under v6; run upgrade-policy and revalidate all gates")

    if not state.get("requirements"):
        errors.append("No requirements recorded")
    if not state.get("tasks"):
        errors.append("No implementation tasks recorded")
    for task_id, task in state.get("tasks", {}).items():
        if task.get("status") != "completed":
            errors.append(f"Task is not complete: {task_id}")
    for phase in PHASES:
        status = state.get("phases", {}).get(phase, {}).get("status")
        if phase in REQUIRED_PHASES and status != "passed":
            errors.append(f"Required phase has not passed: {phase}")
        if phase in OPTIONAL_PHASES and status not in {"passed", "skipped"}:
            errors.append(f"Optional phase needs pass or documented skip: {phase}")
        if status == "passed":
            errors.extend(
                phase_capability_errors(
                    root,
                    state,
                    phase,
                    require_current_workspace=phase in {"implementation", "integration", "security"},
                )
            )
            errors.extend(
                phase_check_errors(
                    root,
                    state,
                    phase,
                    require_current_workspace=phase in {"implementation", "integration", "security"},
                )
            )
            errors.extend(phase_summary_evidence_errors(root, state, phase))
            errors.extend(project_tooling_errors(root, state, phase))
    current_fingerprint = workspace_fingerprint(root)
    for phase in ("integration", "security"):
        phase_state = state.get("phases", {}).get(phase, {})
        if phase_state.get("status") == "passed" and phase_state.get("workspaceFingerprint") != current_fingerprint:
            errors.append(f"{phase} gate evidence is stale for the current workspace")
    for risk in state.get("risks", []):
        severity = risk.get("severity")
        status = risk.get("status", "open")
        if severity in {"critical", "high"} and status != "closed":
            errors.append(f"Unresolved {severity} risk: {risk.get('id')}")
        if severity == "medium" and status not in {"closed", "mitigated", "accepted"}:
            errors.append(f"Unresolved medium risk: {risk.get('id')}")
    if state.get("phases", {}).get("security", {}).get("status") == "passed":
        errors.extend(security_classification_errors(root, state))
    return errors


def require_current_phase(state: dict[str, Any], phase: str) -> None:
    if state.get("currentPhase") != phase:
        raise WorkflowError(f"Current phase is {state.get('currentPhase')}; cannot operate on {phase}")


def command_init(root: Path, args: argparse.Namespace) -> None:
    path = state_path(root)
    if path.exists() and not args.force:
        raise WorkflowError(f"State already exists: {path}. Use status or --force after preserving it.")
    timestamp = now()
    phases = {
        phase: {
            "status": "in_progress" if phase == "contract" else "pending",
            "summary": None,
            "evidence": [],
            "evidenceSha256": None,
            "checks": [],
            "workspaceFingerprint": None,
        }
        for phase in PHASES
    }
    state: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "policyVersion": POLICY_VERSION,
        "workflow": WORKFLOW,
        "skillVersion": SKILL_VERSION,
        "runId": str(uuid.uuid4()),
        "mode": args.mode,
        "status": "active",
        "projectRoot": ".",
        "createdAt": timestamp,
        "updatedAt": timestamp,
        "currentPhase": "contract",
        "currentTask": None,
        "nextAction": "Create the acceptance contract and record requirements.",
        "artifacts": {
            "contract": ".agent/acceptance-contract.md",
            "plan": ".agent/implementation-plan.md",
            "evidenceDirectory": ".agent/evidence",
        },
        "phases": phases,
        "requirements": {},
        "tasks": {},
        "risks": [],
        "skillsUsed": [],
        "capabilityFallbacks": [],
        "securityClassification": None,
        "audit": [],
    }
    audit(state, "workflow-initialized", mode=args.mode)
    save_state(root, state)
    print(f"Initialized {path}")


def command_upgrade_policy(root: Path, _args: argparse.Namespace) -> None:
    state = load_state(root)
    if uses_enforced_policy(state):
        print("Workflow already uses the current policy")
        return
    for task in state.get("tasks", {}).values():
        if task.get("status") == "completed":
            invalidate_task(task, "Upgraded to v6 evidence policy")
    state["schemaVersion"] = SCHEMA_VERSION
    state["policyVersion"] = POLICY_VERSION
    state["skillVersion"] = SKILL_VERSION
    state["currentTask"] = None
    state["skillsUsed"] = []
    state["capabilityFallbacks"] = []
    state["securityClassification"] = None
    reset_phases_from(state, "contract")
    set_next_action(state)
    audit(state, "workflow-policy-upgraded", policyVersion=POLICY_VERSION)
    save_state(root, state)
    print("Upgraded workflow policy; all gates and task evidence require revalidation")


def command_status(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    set_next_action(state)
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return
    print(f"Workflow: {state['workflow']} v{state.get('skillVersion')} ({state['mode']})")
    print(f"Status: {state['status']} | Phase: {state['currentPhase']} | Task: {state.get('currentTask') or '-'}")
    print(f"Requirements: {len(state.get('requirements', {}))} | Tasks: {len(state.get('tasks', {}))}")
    for phase in PHASES:
        print(f"  {phase:14} {state['phases'][phase]['status']}")
    print(f"Next: {state['nextAction']}")


def command_add_requirement(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    requirement_id = args.requirement_id.upper()
    if not (requirement_id.startswith("FR-") or requirement_id.startswith("NFR-")):
        raise WorkflowError("Requirement ID must start with FR- or NFR-")
    if requirement_id in state["requirements"] and not args.replace:
        raise WorkflowError(f"Requirement already exists: {requirement_id}. Use --replace deliberately.")
    state["requirements"][requirement_id] = {
        "kind": args.kind,
        "text": args.text.strip(),
        "source": args.source,
        "updatedAt": now(),
    }
    audit(state, "requirement-recorded", requirement=requirement_id, replace=args.replace)
    save_state(root, state)
    print(f"Recorded {requirement_id}")


def command_add_task(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    task_id = args.task_id.upper()
    if not task_id.startswith("T-"):
        raise WorkflowError("Task ID must start with T-")
    if task_id in state["tasks"] and not args.replace:
        raise WorkflowError(f"Task already exists: {task_id}. Use --replace deliberately.")
    requirements = [item.upper() for item in split_csv(args.requirements)]
    files = [normalize_rel(item) for item in split_csv(args.files)]
    depends_on = [item.upper() for item in split_csv(args.depends_on)]
    expected_checks = split_csv(args.checks)
    if not requirements:
        raise WorkflowError("Each task must map to at least one requirement")
    if not files:
        raise WorkflowError("Each task must declare at least one file path")
    unknown = set(requirements) - set(state["requirements"])
    if unknown:
        raise WorkflowError(f"Unknown requirements: {', '.join(sorted(unknown))}")
    task = {
        "title": args.title.strip(),
        "requirements": requirements,
        "files": files,
        "dependsOn": depends_on,
        "expectedChecks": expected_checks,
        "status": "pending",
        "attempts": 0,
        "checks": [],
        "summary": None,
        "startedAt": None,
        "completedAt": None,
        "invalidReason": None,
    }
    state["tasks"][task_id] = task
    audit(state, "task-recorded", task=task_id, replace=args.replace)
    save_state(root, state)
    print(f"Recorded {task_id}")


def command_start_task(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    require_current_phase(state, "implementation")
    task_id = args.task_id.upper()
    task = state["tasks"].get(task_id)
    if not task:
        raise WorkflowError(f"Unknown task: {task_id}")
    if state.get("currentTask") and state["currentTask"] != task_id:
        raise WorkflowError(f"Finish current task first: {state['currentTask']}")
    incomplete = [dep for dep in task.get("dependsOn", []) if state["tasks"].get(dep, {}).get("status") != "completed"]
    if incomplete:
        raise WorkflowError(f"Dependencies are incomplete: {', '.join(incomplete)}")
    task["status"] = "in_progress"
    task["attempts"] = int(task.get("attempts", 0)) + 1
    task["startedAt"] = now()
    task["completedAt"] = None
    task["invalidReason"] = None
    state["currentTask"] = task_id
    set_next_action(state)
    audit(state, "task-started", task=task_id, attempt=task["attempts"])
    save_state(root, state)
    print(f"Started {task_id}")


def command_record_check(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    task_id = args.task_id.upper()
    task = state["tasks"].get(task_id)
    if not task:
        raise WorkflowError(f"Unknown task: {task_id}")
    if task.get("status") != "in_progress" or state.get("currentTask") != task_id:
        raise WorkflowError(f"Start {task_id} before recording checks")
    evidence = normalize_rel(args.evidence)
    evidence_path = resolve_project_path(root, evidence)
    if not evidence_path.is_file():
        raise WorkflowError(f"Evidence file does not exist: {evidence}")
    for previous in task.setdefault("checks", []):
        if previous.get("name") == args.name and previous.get("valid"):
            previous["valid"] = False
            previous["invalidReason"] = "Superseded by a newer result for the same check"
    check = {
        "name": args.name,
        "command": args.command,
        "exitCode": args.exit_code,
        "evidence": evidence,
        "recordedAt": now(),
        "scopeFingerprint": scope_fingerprint(root, task.get("files", [])),
        "evidenceSha256": file_sha256(evidence_path),
        "valid": True,
    }
    task["checks"].append(check)
    audit(state, "check-recorded", task=task_id, name=args.name, exitCode=args.exit_code)
    save_state(root, state)
    outcome = "pass" if args.exit_code == 0 else "fail"
    print(f"Recorded {args.name} for {task_id}: {outcome}")


def command_complete_task(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    task_id = args.task_id.upper()
    task = state["tasks"].get(task_id)
    if not task:
        raise WorkflowError(f"Unknown task: {task_id}")
    if task.get("status") != "in_progress" or state.get("currentTask") != task_id:
        raise WorkflowError(f"Task is not active: {task_id}")
    if not task_fresh(root, task):
        expected = task.get("expectedChecks", [])
        detail = f" including: {', '.join(expected)}" if expected else ""
        raise WorkflowError(f"Task needs fresh passing evidence{detail}; source and evidence files must be unchanged")
    later_failure = False
    for check in reversed(task.get("checks", [])):
        if not check.get("valid"):
            continue
        if check.get("exitCode") != 0:
            later_failure = True
            break
        if check.get("exitCode") == 0:
            break
    if later_failure:
        raise WorkflowError("The latest valid check failed; fix and record a new passing check")
    task["status"] = "completed"
    task["summary"] = args.summary.strip()
    task["completedAt"] = now()
    state["currentTask"] = None
    set_next_action(state)
    audit(state, "task-completed", task=task_id)
    save_state(root, state)
    print(f"Completed {task_id}")


def phase_structural_errors(root: Path, state: dict[str, Any], phase: str) -> list[str]:
    errors = phase_capability_errors(root, state, phase, require_current_workspace=True)
    errors.extend(phase_check_errors(root, state, phase, require_current_workspace=True))
    errors.extend(project_tooling_errors(root, state, phase))
    if phase == "contract" and not state.get("requirements"):
        errors.append("Contract gate requires at least one requirement")
    if phase == "plan":
        errors.extend(coverage_errors(state))
        if not state.get("tasks"):
            errors.append("Plan gate requires at least one task")
    if phase in {"implementation", "integration"}:
        errors.extend(coverage_errors(state))
        for task_id, task in state.get("tasks", {}).items():
            if task.get("status") != "completed":
                errors.append(f"Task is not completed: {task_id}")
            elif not task_fresh(root, task):
                errors.append(f"Task evidence is stale: {task_id}")
    if phase == "security":
        errors.extend(security_classification_errors(root, state))
        for risk in state.get("risks", []):
            severity = risk.get("severity")
            status = risk.get("status")
            if severity in {"critical", "high"} and status != "closed":
                errors.append(f"Security gate blocked by {severity} risk {risk.get('id')}")
            if severity == "medium" and status not in {"closed", "mitigated", "accepted"}:
                errors.append(f"Security gate blocked by medium risk {risk.get('id')}")
    return errors


def command_pass_gate(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    phase = args.phase
    require_current_phase(state, phase)
    if state.get("currentTask"):
        raise WorkflowError(f"Complete current task before passing a gate: {state['currentTask']}")
    evidence = normalize_rel(args.evidence)
    evidence_path = resolve_project_path(root, evidence)
    if not evidence_path.is_file():
        raise WorkflowError(f"Gate evidence file does not exist: {evidence}")
    errors = phase_structural_errors(root, state, phase)
    if errors:
        raise WorkflowError("Gate failed:\n- " + "\n- ".join(errors))
    phase_state = state["phases"][phase]
    phase_state["status"] = "passed"
    phase_state["summary"] = args.summary.strip()
    phase_state["evidence"] = [evidence]
    phase_state["evidenceSha256"] = file_sha256(evidence_path)
    phase_state["workspaceFingerprint"] = workspace_fingerprint(root)
    audit(state, "gate-passed", phase=phase, evidence=evidence)
    advance_after_gate(state, phase)
    save_state(root, state)
    print(f"Passed {phase} gate")


def command_skip_phase(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    phase = args.phase
    if phase not in OPTIONAL_PHASES:
        raise WorkflowError(f"Phase cannot be skipped: {phase}")
    require_current_phase(state, phase)
    phase_state = state["phases"][phase]
    phase_state["status"] = "skipped"
    phase_state["summary"] = args.reason.strip()
    phase_state["evidence"] = []
    phase_state["workspaceFingerprint"] = workspace_fingerprint(root)
    audit(state, "phase-skipped", phase=phase, reason=args.reason.strip())
    advance_after_gate(state, phase)
    save_state(root, state)
    print(f"Skipped {phase}: {args.reason.strip()}")


def invalidate_task(task: dict[str, Any], reason: str) -> None:
    task["status"] = "pending"
    task["completedAt"] = None
    task["invalidReason"] = reason
    for check in task.get("checks", []):
        check["valid"] = False


def reset_phases_from(state: dict[str, Any], phase: str) -> None:
    start = phase_index(phase)
    for item in PHASES[start:]:
        state["phases"][item] = {
            "status": "in_progress" if item == phase else "pending",
            "summary": None,
            "evidence": [],
            "evidenceSha256": None,
            "checks": [],
            "workspaceFingerprint": None,
        }
    for entry in [*state.get("skillsUsed", []), *state.get("capabilityFallbacks", [])]:
        entry_phase = entry.get("phase")
        if entry_phase in PHASES and phase_index(entry_phase) >= start:
            entry["valid"] = False
    if phase_index(phase) <= phase_index("security"):
        state["securityClassification"] = None
    state["currentPhase"] = phase
    state["status"] = "active"


def command_invalidate(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    reason = args.reason.strip()
    changed_files = {normalize_rel(item) for item in split_csv(args.files)}
    affected: list[str] = []
    if changed_files:
        for task_id, task in state.get("tasks", {}).items():
            if task_id == state.get("currentTask"):
                continue
            if changed_files.intersection(task.get("files", [])) and task.get("status") == "completed":
                invalidate_task(task, reason)
                affected.append(task_id)
        if affected and phase_index(state["currentPhase"]) > phase_index("implementation"):
            reset_phases_from(state, "implementation")
        elif affected:
            for phase in ("integration", "security"):
                state["phases"][phase] = {
                    "status": "pending",
                    "summary": None,
                    "evidence": [],
                    "evidenceSha256": None,
                    "checks": [],
                    "workspaceFingerprint": None,
                }
            for entry in [*state.get("skillsUsed", []), *state.get("capabilityFallbacks", [])]:
                if entry.get("phase") in {"integration", "security"}:
                    entry["valid"] = False
            state["securityClassification"] = None
    if args.phase:
        reset_phases_from(state, args.phase)
        if phase_index(args.phase) <= phase_index("implementation"):
            for task_id, task in state.get("tasks", {}).items():
                if task.get("status") == "completed":
                    invalidate_task(task, reason)
                    if task_id not in affected:
                        affected.append(task_id)
            state["currentTask"] = None
    if not changed_files and not args.phase:
        raise WorkflowError("Provide --files and/or --phase")
    set_next_action(state)
    audit(state, "workflow-invalidated", phase=args.phase, files=sorted(changed_files), tasks=affected, reason=reason)
    save_state(root, state)
    print(f"Invalidated {len(affected)} task(s)" + (f" from phase {args.phase}" if args.phase else ""))


def command_add_risk(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    risk_id = args.risk_id.upper()
    if args.severity not in SEVERITIES:
        raise WorkflowError(f"Invalid severity: {args.severity}")
    existing = next((risk for risk in state["risks"] if risk.get("id") == risk_id), None)
    if existing and not args.replace:
        raise WorkflowError(f"Risk already exists: {risk_id}. Use --replace deliberately.")
    risk = {
        "id": risk_id,
        "severity": args.severity,
        "title": args.title.strip(),
        "status": args.status,
        "evidence": normalize_rel(args.evidence) if args.evidence else None,
        "updatedAt": now(),
    }
    if existing:
        state["risks"][state["risks"].index(existing)] = risk
    else:
        state["risks"].append(risk)
    audit(state, "risk-recorded", risk=risk_id, severity=args.severity, status=args.status)
    save_state(root, state)
    print(f"Recorded risk {risk_id}")


def command_log_skill(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    phase = state.get("currentPhase")
    resources = split_csv(args.resources)
    if uses_enforced_policy(state) and "SKILL.md" not in resources:
        raise WorkflowError("log-skill requires --resources SKILL.md to prove the skill instructions were loaded")
    skill_file = Path(args.skill_file).expanduser().resolve()
    if not skill_file.is_file() or skill_file.name != "SKILL.md":
        raise WorkflowError(f"--skill-file must point to an existing SKILL.md: {skill_file}")
    actual_name = skill_frontmatter_name(skill_file)
    if actual_name != args.name:
        raise WorkflowError(f"Skill name mismatch: command={args.name!r}, frontmatter={actual_name!r}")
    for previous in state.setdefault("skillsUsed", []):
        if previous.get("phase") == phase and previous.get("name") == args.name and previous.get("valid", True):
            previous["valid"] = False
            previous["invalidReason"] = "Superseded by a newer activation record"
    entry = {
        "name": args.name,
        "version": args.version,
        "phase": phase,
        "loadedAt": now(),
        "resources": resources,
        "source": args.source,
        "skillFile": str(skill_file),
        "skillFileSha256": file_sha256(skill_file),
        "valid": True,
    }
    state["skillsUsed"].append(entry)
    audit(state, "skill-loaded", skill=args.name, version=args.version)
    save_state(root, state)
    print(f"Logged skill {args.name}")


def command_log_fallback(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    phase = state.get("currentPhase")
    expected_reference = PHASE_FALLBACK_REFERENCES[phase]
    reference = normalize_rel(args.reference)
    if reference != expected_reference:
        raise WorkflowError(f"{phase} fallback must use {expected_reference}")
    if not (Path(__file__).resolve().parent.parent / reference).is_file():
        raise WorkflowError(f"Bundled fallback reference does not exist: {reference}")
    missing_skills = split_csv(args.missing_skills)
    allowed = {name for group in PHASE_SKILL_GROUPS[phase] for name in group}
    if not missing_skills or not set(missing_skills).issubset(allowed):
        raise WorkflowError(f"Fallback must name unavailable {phase} skills from: {', '.join(sorted(allowed))}")
    if len(args.reason.strip()) < 12:
        raise WorkflowError("Fallback reason must explain why native skill loading was unavailable")
    discovery = normalize_rel(args.discovery_evidence)
    discovery_path = resolve_project_path(root, discovery)
    if not discovery_path.is_file():
        raise WorkflowError(f"Skill discovery evidence does not exist: {discovery}")
    for previous in state.setdefault("capabilityFallbacks", []):
        if (
            previous.get("phase") == phase
            and set(previous.get("missingSkills", [])).intersection(missing_skills)
            and previous.get("valid", True)
        ):
            previous["valid"] = False
            previous["invalidReason"] = "Superseded by newer discovery evidence"
    entry = {
        "phase": phase,
        "missingSkills": missing_skills,
        "reason": args.reason.strip(),
        "reference": reference,
        "evidence": discovery,
        "evidenceSha256": file_sha256(discovery_path),
        "workspaceFingerprint": workspace_fingerprint(root),
        "recordedAt": now(),
        "valid": True,
    }
    state["capabilityFallbacks"].append(entry)
    audit(state, "capability-fallback-recorded", phase=phase, skills=missing_skills, evidence=discovery)
    save_state(root, state)
    print(f"Recorded {phase} capability fallback")


def command_record_gate_check(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    phase = args.phase
    require_current_phase(state, phase)
    evidence = normalize_rel(args.evidence)
    evidence_path = resolve_project_path(root, evidence)
    if not evidence_path.is_file():
        raise WorkflowError(f"Gate check evidence does not exist: {evidence}")
    if args.kind == "automated" and (not args.command or args.exit_code is None):
        raise WorkflowError("Automated gate checks require --command and --exit-code")
    if args.kind != "automated" and args.exit_code not in (None, 0):
        raise WorkflowError("Manual and not-applicable checks cannot record a failing exit code")
    if args.kind == "not-applicable" and len(args.summary.strip()) < 12:
        raise WorkflowError("Not-applicable checks require a concrete explanation")
    phase_checks = state["phases"][phase].setdefault("checks", [])
    for previous in phase_checks:
        if previous.get("name") == args.name and previous.get("valid"):
            previous["valid"] = False
            previous["invalidReason"] = "Superseded by a newer result for the same check"
    check = {
        "name": args.name,
        "kind": args.kind,
        "command": args.command,
        "exitCode": args.exit_code,
        "evidence": evidence,
        "summary": args.summary.strip(),
        "recordedAt": now(),
        "workspaceFingerprint": workspace_fingerprint(root),
        "evidenceSha256": file_sha256(evidence_path),
        "valid": True,
    }
    phase_checks.append(check)
    audit(state, "gate-check-recorded", phase=phase, name=args.name, kind=args.kind, exitCode=args.exit_code)
    save_state(root, state)
    outcome = "pass" if args.kind != "automated" or args.exit_code == 0 else "fail"
    print(f"Recorded {phase}/{args.name}: {outcome}")


def command_classify_security(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    require_current_phase(state, "security")
    evidence = normalize_rel(args.evidence)
    evidence_path = resolve_project_path(root, evidence)
    if not evidence_path.is_file():
        raise WorkflowError(f"Security classification evidence does not exist: {evidence}")
    if len(args.reason.strip()) < 12:
        raise WorkflowError("Security classification requires a concrete data-flow and attack-surface reason")
    state["securityClassification"] = {
        "level": args.level,
        "reason": args.reason.strip(),
        "evidence": evidence,
        "evidenceSha256": file_sha256(evidence_path),
        "workspaceFingerprint": workspace_fingerprint(root),
        "recordedAt": now(),
    }
    audit(state, "security-classified", level=args.level, evidence=evidence)
    save_state(root, state)
    print(f"Classified security risk as {args.level}")


def command_verify(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    errors = validate_state(root, state, for_finish=args.finish)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise WorkflowError(f"Verification failed with {len(errors)} error(s)")
    print("Workflow state is valid" + (" for finish" if args.finish else ""))


def command_finish(root: Path, _args: argparse.Namespace) -> None:
    state = load_state(root)
    errors = validate_state(root, state, for_finish=True)
    if errors:
        raise WorkflowError("Cannot finish:\n- " + "\n- ".join(errors))
    state["status"] = "done"
    state["currentTask"] = None
    set_next_action(state)
    audit(state, "workflow-finished", fingerprint=workspace_fingerprint(root))
    save_state(root, state)
    print("Workflow finished with all required gates satisfied")


def parser() -> argparse.ArgumentParser:
    root_parser = argparse.ArgumentParser(description=__doc__)
    root_parser.add_argument("--root", default=".", help="Project root; state is stored under .agent/")
    commands = root_parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--mode", choices=("full", "targeted"), default="full")
    init.add_argument("--force", action="store_true")
    init.set_defaults(handler=command_init)

    upgrade = commands.add_parser("upgrade-policy")
    upgrade.set_defaults(handler=command_upgrade_policy)

    status = commands.add_parser("status")
    status.add_argument("--json", action="store_true")
    status.set_defaults(handler=command_status)

    requirement = commands.add_parser("add-requirement")
    requirement.add_argument("requirement_id")
    requirement.add_argument("--kind", choices=("functional", "nonfunctional"), required=True)
    requirement.add_argument("--text", required=True)
    requirement.add_argument("--source", default="user")
    requirement.add_argument("--replace", action="store_true")
    requirement.set_defaults(handler=command_add_requirement)

    task = commands.add_parser("add-task")
    task.add_argument("task_id")
    task.add_argument("--title", required=True)
    task.add_argument("--requirements", action="append", required=True)
    task.add_argument("--files", action="append", required=True)
    task.add_argument("--depends-on", action="append", default=[])
    task.add_argument("--checks", action="append", default=[], help="Expected check names; all must pass before completion")
    task.add_argument("--replace", action="store_true")
    task.set_defaults(handler=command_add_task)

    start = commands.add_parser("start-task")
    start.add_argument("task_id")
    start.set_defaults(handler=command_start_task)

    check = commands.add_parser("record-check")
    check.add_argument("task_id")
    check.add_argument("--name", required=True)
    check.add_argument("--command", required=True)
    check.add_argument("--exit-code", type=int, required=True)
    check.add_argument("--evidence", required=True)
    check.set_defaults(handler=command_record_check)

    complete = commands.add_parser("complete-task")
    complete.add_argument("task_id")
    complete.add_argument("--summary", required=True)
    complete.set_defaults(handler=command_complete_task)

    gate = commands.add_parser("pass-gate")
    gate.add_argument("phase", choices=PHASES)
    gate.add_argument("--evidence", required=True)
    gate.add_argument("--summary", required=True)
    gate.set_defaults(handler=command_pass_gate)

    skip = commands.add_parser("skip-phase")
    skip.add_argument("phase", choices=tuple(sorted(OPTIONAL_PHASES)))
    skip.add_argument("--reason", required=True)
    skip.set_defaults(handler=command_skip_phase)

    invalidate = commands.add_parser("invalidate")
    invalidate.add_argument("--files", action="append", default=[])
    invalidate.add_argument("--phase", choices=PHASES)
    invalidate.add_argument("--reason", required=True)
    invalidate.set_defaults(handler=command_invalidate)

    risk = commands.add_parser("add-risk")
    risk.add_argument("risk_id")
    risk.add_argument("--severity", choices=tuple(sorted(SEVERITIES)), required=True)
    risk.add_argument("--title", required=True)
    risk.add_argument("--status", choices=("open", "mitigated", "accepted", "closed"), default="open")
    risk.add_argument("--evidence")
    risk.add_argument("--replace", action="store_true")
    risk.set_defaults(handler=command_add_risk)

    skill = commands.add_parser("log-skill")
    skill.add_argument("name")
    skill.add_argument("--skill-file", required=True)
    skill.add_argument("--version")
    skill.add_argument("--resources", action="append", default=[])
    skill.add_argument("--source", choices=("native", "bridge", "manual"), default="native")
    skill.set_defaults(handler=command_log_skill)

    fallback = commands.add_parser("log-fallback")
    fallback.add_argument("--missing-skills", action="append", required=True)
    fallback.add_argument("--reason", required=True)
    fallback.add_argument("--reference", required=True)
    fallback.add_argument("--discovery-evidence", required=True)
    fallback.set_defaults(handler=command_log_fallback)

    gate_check = commands.add_parser("record-gate-check")
    gate_check.add_argument("phase", choices=PHASES)
    gate_check.add_argument("--name", required=True)
    gate_check.add_argument("--kind", choices=tuple(sorted(CHECK_KINDS)), required=True)
    gate_check.add_argument("--command")
    gate_check.add_argument("--exit-code", type=int)
    gate_check.add_argument("--evidence", required=True)
    gate_check.add_argument("--summary", required=True)
    gate_check.set_defaults(handler=command_record_gate_check)

    security_classification = commands.add_parser("classify-security")
    security_classification.add_argument("--level", choices=("low", "medium", "high"), required=True)
    security_classification.add_argument("--reason", required=True)
    security_classification.add_argument("--evidence", required=True)
    security_classification.set_defaults(handler=command_classify_security)

    verify = commands.add_parser("verify")
    verify.add_argument("--finish", action="store_true")
    verify.set_defaults(handler=command_verify)

    finish = commands.add_parser("finish")
    finish.set_defaults(handler=command_finish)
    return root_parser


def main(argv: Optional[list[str]] = None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: Project root does not exist: {root}", file=sys.stderr)
        return 2
    try:
        args.handler(root, args)
        return 0
    except WorkflowError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
