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
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Optional


SCHEMA_VERSION = 1
SKILL_VERSION = "5.0.0"
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
    if state.get("schemaVersion") != SCHEMA_VERSION or state.get("workflow") != WORKFLOW:
        raise WorkflowError("Unsupported or unrelated workflow-state.json")
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
            "workspaceFingerprint": None,
        }
        for phase in PHASES
    }
    state: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
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
        "audit": [],
    }
    audit(state, "workflow-initialized", mode=args.mode)
    save_state(root, state)
    print(f"Initialized {path}")


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
    task.setdefault("checks", []).append(check)
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
    if phase == "contract" and not state.get("requirements"):
        return ["Contract gate requires at least one requirement"]
    if phase == "plan":
        errors = coverage_errors(state)
        if not state.get("tasks"):
            errors.append("Plan gate requires at least one task")
        return errors
    if phase in {"implementation", "integration"}:
        errors = coverage_errors(state)
        for task_id, task in state.get("tasks", {}).items():
            if task.get("status") != "completed":
                errors.append(f"Task is not completed: {task_id}")
            elif not task_fresh(root, task):
                errors.append(f"Task evidence is stale: {task_id}")
        return errors
    if phase == "security":
        errors: list[str] = []
        for risk in state.get("risks", []):
            severity = risk.get("severity")
            status = risk.get("status")
            if severity in {"critical", "high"} and status != "closed":
                errors.append(f"Security gate blocked by {severity} risk {risk.get('id')}")
            if severity == "medium" and status not in {"closed", "mitigated", "accepted"}:
                errors.append(f"Security gate blocked by medium risk {risk.get('id')}")
        return errors
    return []


def command_pass_gate(root: Path, args: argparse.Namespace) -> None:
    state = load_state(root)
    phase = args.phase
    require_current_phase(state, phase)
    if state.get("currentTask"):
        raise WorkflowError(f"Complete current task before passing a gate: {state['currentTask']}")
    evidence = normalize_rel(args.evidence)
    if not resolve_project_path(root, evidence).is_file():
        raise WorkflowError(f"Gate evidence file does not exist: {evidence}")
    errors = phase_structural_errors(root, state, phase)
    if errors:
        raise WorkflowError("Gate failed:\n- " + "\n- ".join(errors))
    phase_state = state["phases"][phase]
    phase_state["status"] = "passed"
    phase_state["summary"] = args.summary.strip()
    phase_state["evidence"] = [evidence]
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
            "workspaceFingerprint": None,
        }
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
                    "workspaceFingerprint": None,
                }
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
    entry = {
        "name": args.name,
        "version": args.version,
        "phase": state.get("currentPhase"),
        "loadedAt": now(),
        "resources": split_csv(args.resources),
    }
    state.setdefault("skillsUsed", []).append(entry)
    audit(state, "skill-loaded", skill=args.name, version=args.version)
    save_state(root, state)
    print(f"Logged skill {args.name}")


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
    skill.add_argument("--version")
    skill.add_argument("--resources", action="append", default=[])
    skill.set_defaults(handler=command_log_skill)

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
