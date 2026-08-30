#!/usr/bin/env python3
"""Deterministic runtime-state helper for tiered-agent-orchestrator."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Optional


SCHEMA_VERSION = 1
RUNTIME_NAME = ".tiered-agent"
SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "runtime"
PHASES = {"planning", "execution", "review", "complete"}
PROJECT_STATUSES = {"active", "blocked", "waiting-owner", "complete"}
WORKER_STATUSES = {
    "ready",
    "active",
    "blocked",
    "waiting-owner",
    "completed",
    "inactive",
}
REVIEW_STATUSES = {"not-requested", "ready", "active", "blocked", "completed"}
REVIEW_LEVELS = {"none", "balanced", "strong"}
PROJECT_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
WORKER_ID_RE = re.compile(r"^worker-[1-9][0-9]*$")
REVIEWER_ID_RE = re.compile(r"^reviewer-[1-9][0-9]*$")


class StateError(RuntimeError):
    """Raised for an invalid or unsafe state operation."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_root(value: str) -> Path:
    return Path(value).expanduser().resolve()


def runtime_dir(root: Path) -> Path:
    return root / RUNTIME_NAME


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StateError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StateError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateError(f"Expected a JSON object in {path}")
    return value


def read_template_text(name: str) -> str:
    path = TEMPLATE_ROOT / name
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise StateError(f"Skill template is missing: {path}") from exc


def read_template_json(name: str) -> dict[str, Any]:
    path = TEMPLATE_ROOT / name
    return read_json(path)


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_new_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise StateError(f"Refusing to overwrite existing file: {path}") from exc


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    write_new_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def require_nonempty(value: str, label: str) -> str:
    result = value.strip()
    if not result:
        raise StateError(f"{label} must not be empty")
    return result


def check_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def checked_relative_path(runtime: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise StateError(f"{label} must be a non-empty relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or value != pure.as_posix():
        raise StateError(f"{label} must be a normalized path inside {RUNTIME_NAME}: {value}")
    candidate = (runtime / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(runtime.resolve())
    except ValueError as exc:
        raise StateError(f"{label} escapes {RUNTIME_NAME}: {value}") from exc
    return candidate


def state_path(runtime: Path) -> Path:
    return runtime / "STATE.json"


def load_state(runtime: Path) -> dict[str, Any]:
    return read_json(state_path(runtime))


def save_state(runtime: Path, state: dict[str, Any]) -> None:
    state["last_updated"] = utc_now()
    atomic_write_json(state_path(runtime), state)


def validate_status_object(
    value: dict[str, Any], expected_id: str, path: Path
) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "worker_id",
        "status",
        "summary",
        "files_changed",
        "verification",
        "next_action",
        "last_updated",
    }
    missing = sorted(required - value.keys())
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
        return errors
    if value["schema_version"] != SCHEMA_VERSION:
        errors.append(f"{path}: unsupported schema_version")
    if value["worker_id"] != expected_id:
        errors.append(f"{path}: worker_id does not match registry")
    if value["status"] not in WORKER_STATUSES:
        errors.append(f"{path}: invalid worker status {value['status']!r}")
    for key in ("summary", "next_action"):
        if not isinstance(value[key], str):
            errors.append(f"{path}: {key} must be a string")
    for key in ("files_changed", "verification"):
        if not isinstance(value[key], list) or not all(isinstance(item, str) for item in value[key]):
            errors.append(f"{path}: {key} must be a list of strings")
    if not check_timestamp(value["last_updated"]):
        errors.append(f"{path}: last_updated must be an ISO-8601 UTC timestamp")
    return errors


def validate_review_status(value: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "reviewer_id",
        "status",
        "summary",
        "verification",
        "last_updated",
    }
    missing = sorted(required - value.keys())
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(missing)}")
        return errors
    if value["schema_version"] != SCHEMA_VERSION:
        errors.append(f"{path}: unsupported schema_version")
    reviewer_id = value["reviewer_id"]
    if reviewer_id is not None and (
        not isinstance(reviewer_id, str) or not REVIEWER_ID_RE.fullmatch(reviewer_id)
    ):
        errors.append(f"{path}: invalid reviewer_id")
    if value["status"] not in REVIEW_STATUSES:
        errors.append(f"{path}: invalid review status {value['status']!r}")
    if not isinstance(value["summary"], str):
        errors.append(f"{path}: summary must be a string")
    if not isinstance(value["verification"], list) or not all(
        isinstance(item, str) for item in value["verification"]
    ):
        errors.append(f"{path}: verification must be a list of strings")
    if not check_timestamp(value["last_updated"]):
        errors.append(f"{path}: last_updated must be an ISO-8601 UTC timestamp")
    return errors


def validate_runtime(runtime: Path) -> list[str]:
    errors: list[str] = []
    for name in ("STATE.json", "PLAN.md", "OWNER_DIRECTIVES.md", "HANDOFF.md"):
        if not (runtime / name).is_file():
            errors.append(f"Missing required file: {runtime / name}")
    for name in ("workers", "inbox/owner", "review"):
        if not (runtime / name).is_dir():
            errors.append(f"Missing required directory: {runtime / name}")
    if errors:
        return errors

    try:
        state = load_state(runtime)
    except StateError as exc:
        return [str(exc)]

    required = {
        "schema_version",
        "project_id",
        "phase",
        "status",
        "profile",
        "current_milestone",
        "workers",
        "review",
        "last_updated",
        "next_action",
    }
    missing = sorted(required - state.keys())
    if missing:
        errors.append(f"STATE.json: missing fields: {', '.join(missing)}")
        return errors

    if state["schema_version"] != SCHEMA_VERSION:
        errors.append("STATE.json: unsupported schema_version")
    if not isinstance(state["project_id"], str) or not PROJECT_ID_RE.fullmatch(state["project_id"]):
        errors.append("STATE.json: invalid project_id")
    if state["phase"] not in PHASES:
        errors.append(f"STATE.json: invalid phase {state['phase']!r}")
    if state["status"] not in PROJECT_STATUSES:
        errors.append(f"STATE.json: invalid status {state['status']!r}")
    if (state["phase"] == "complete") != (state["status"] == "complete"):
        errors.append("STATE.json: phase and status must both be complete or both be non-complete")
    for key in ("profile", "current_milestone"):
        if not isinstance(state[key], str) or not state[key].strip():
            errors.append(f"STATE.json: {key} must be a non-empty string")
    if not check_timestamp(state["last_updated"]):
        errors.append("STATE.json: last_updated must be an ISO-8601 UTC timestamp")

    next_action = state["next_action"]
    if not isinstance(next_action, dict) or set(next_action) != {"actor", "instruction"}:
        errors.append("STATE.json: next_action must contain only actor and instruction")
    elif not all(isinstance(next_action[key], str) and next_action[key].strip() for key in next_action):
        errors.append("STATE.json: next_action values must be non-empty strings")

    workers = state["workers"]
    if not isinstance(workers, list):
        errors.append("STATE.json: workers must be a list")
        workers = []

    seen_ids: set[str] = set()
    registry: dict[str, dict[str, Any]] = {}
    active_scopes: dict[str, str] = {}
    for index, worker in enumerate(workers):
        prefix = f"STATE.json: workers[{index}]"
        if not isinstance(worker, dict):
            errors.append(f"{prefix} must be an object")
            continue
        worker_required = {"id", "task_path", "status_path", "write_scope", "depends_on"}
        if set(worker) != worker_required:
            errors.append(f"{prefix} must contain exactly {', '.join(sorted(worker_required))}")
            continue
        worker_id = worker["id"]
        if not isinstance(worker_id, str) or not WORKER_ID_RE.fullmatch(worker_id):
            errors.append(f"{prefix}.id is invalid")
            continue
        if worker_id in seen_ids:
            errors.append(f"{prefix}.id is duplicated: {worker_id}")
            continue
        seen_ids.add(worker_id)
        registry[worker_id] = worker
        for key in ("write_scope", "depends_on"):
            if not isinstance(worker[key], list) or not all(isinstance(item, str) for item in worker[key]):
                errors.append(f"{prefix}.{key} must be a list of strings")

        try:
            task = checked_relative_path(runtime, worker["task_path"], f"{prefix}.task_path")
            status_file = checked_relative_path(runtime, worker["status_path"], f"{prefix}.status_path")
        except StateError as exc:
            errors.append(str(exc))
            continue
        if not task.is_file():
            errors.append(f"{prefix}: task file does not exist: {task}")
        if not status_file.is_file():
            errors.append(f"{prefix}: status file does not exist: {status_file}")
            continue
        try:
            status_value = read_json(status_file)
        except StateError as exc:
            errors.append(str(exc))
            continue
        errors.extend(validate_status_object(status_value, worker_id, status_file))
        if status_value.get("status") == "active":
            for dependency in worker.get("depends_on", []):
                dependency_entry = registry.get(dependency)
                if dependency_entry is None:
                    continue
                try:
                    dependency_status_path = checked_relative_path(
                        runtime,
                        dependency_entry["status_path"],
                        f"{worker_id}.dependency.status_path",
                    )
                    dependency_status = read_json(dependency_status_path).get("status")
                except StateError as exc:
                    errors.append(str(exc))
                    continue
                if dependency_status not in {"completed", "inactive"}:
                    errors.append(
                        f"Active Worker {worker_id} has incomplete dependency "
                        f"{dependency} ({dependency_status})"
                    )
        if status_value.get("status") in {"ready", "active", "blocked", "waiting-owner"}:
            for scope in worker.get("write_scope", []):
                if scope in active_scopes:
                    errors.append(
                        f"Active write scope {scope!r} is shared by {active_scopes[scope]} and {worker_id}"
                    )
                else:
                    active_scopes[scope] = worker_id

    for worker_id, worker in registry.items():
        for dependency in worker.get("depends_on", []):
            if dependency == worker_id:
                errors.append(f"{worker_id} cannot depend on itself")
            elif dependency not in registry:
                errors.append(f"{worker_id} depends on unknown Worker {dependency}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(worker_id: str) -> None:
        if worker_id in visiting:
            errors.append(f"Worker dependency cycle includes {worker_id}")
            return
        if worker_id in visited or worker_id not in registry:
            return
        visiting.add(worker_id)
        for dependency in registry[worker_id].get("depends_on", []):
            visit(dependency)
        visiting.remove(worker_id)
        visited.add(worker_id)

    for worker_id in registry:
        visit(worker_id)

    review = state["review"]
    review_required_fields = {
        "required",
        "level",
        "reviewer_id",
        "task_path",
        "status_path",
        "report_path",
    }
    if not isinstance(review, dict) or set(review) != review_required_fields:
        errors.append("STATE.json: review has invalid fields")
    else:
        if not isinstance(review["required"], bool):
            errors.append("STATE.json: review.required must be boolean")
        if review["level"] not in REVIEW_LEVELS:
            errors.append("STATE.json: review.level is invalid")
        if review["required"] != (review["level"] != "none"):
            errors.append("STATE.json: review.required and review.level disagree")
        reviewer_id = review["reviewer_id"]
        if reviewer_id is not None and (
            not isinstance(reviewer_id, str) or not REVIEWER_ID_RE.fullmatch(reviewer_id)
        ):
            errors.append("STATE.json: review.reviewer_id is invalid")
        if review["required"] and reviewer_id is None:
            errors.append("STATE.json: required review must name a reviewer")
        for key in ("task_path", "status_path", "report_path"):
            try:
                target = checked_relative_path(runtime, review[key], f"review.{key}")
            except StateError as exc:
                errors.append(str(exc))
                continue
            if not target.is_file():
                errors.append(f"Missing review file: {target}")
        try:
            review_status_path = checked_relative_path(runtime, review["status_path"], "review.status_path")
            if review_status_path.is_file():
                review_status = read_json(review_status_path)
                errors.extend(validate_review_status(review_status, review_status_path))
                if reviewer_id != review_status.get("reviewer_id"):
                    errors.append("STATE.json and review/STATUS.json reviewer_id disagree")
        except StateError as exc:
            errors.append(str(exc))

    return errors


def assert_valid(runtime: Path) -> None:
    errors = validate_runtime(runtime)
    if errors:
        raise StateError("Runtime validation failed:\n- " + "\n- ".join(errors))


def command_init(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    runtime = runtime_dir(root)
    if not PROJECT_ID_RE.fullmatch(args.project_id):
        raise StateError("project-id must use lowercase letters, digits, and single hyphens")
    profile = require_nonempty(args.profile, "profile")
    if runtime.exists():
        if state_path(runtime).is_file():
            assert_valid(runtime)
            print(f"Already initialized; no files changed: {runtime}")
            return 0
        raise StateError(f"Refusing to overwrite partial runtime directory: {runtime}")

    (runtime / "workers").mkdir(parents=True)
    (runtime / "inbox" / "owner").mkdir(parents=True)
    (runtime / "review").mkdir(parents=True)

    now = utc_now()
    state = read_template_json("STATE.json")
    state["project_id"] = args.project_id
    state["profile"] = profile
    state["last_updated"] = now
    write_new_json(state_path(runtime), state)

    replacements = {"{{PROJECT_ID}}": args.project_id}
    for source, destination in (
        ("PLAN.md", runtime / "PLAN.md"),
        ("OWNER_DIRECTIVES.md", runtime / "OWNER_DIRECTIVES.md"),
        ("HANDOFF.md", runtime / "HANDOFF.md"),
        ("review-task.md", runtime / "review" / "TASK.md"),
        ("review-report.md", runtime / "review" / "REPORT.md"),
    ):
        content = read_template_text(source)
        for old, new in replacements.items():
            content = content.replace(old, new)
        write_new_text(destination, content)

    review_status = read_template_json("review-status.json")
    review_status["last_updated"] = now
    write_new_json(runtime / "review" / "STATUS.json", review_status)
    assert_valid(runtime)
    print(f"Initialized {runtime}")
    return 0


def markdown_list(values: Iterable[str]) -> str:
    items = list(values)
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def build_worker_task(args: argparse.Namespace) -> str:
    coordination = args.coordination_justification or "Not required."
    return (
        f"# Worker Task: {args.worker_id}\n\n"
        f"## Objective\n\n{args.objective.strip()}\n\n"
        f"## Allowed scope\n\n{markdown_list(args.allowed_scope)}\n\n"
        f"## Read dependencies\n\n{markdown_list(args.read_dependency)}\n\n"
        f"## Do not modify\n\n{markdown_list(args.do_not_modify)}\n\n"
        f"## Worker dependencies\n\n{markdown_list(args.depends_on)}\n\n"
        f"## Relevant plan sections\n\n{markdown_list(args.plan_section)}\n\n"
        f"## Completion criteria\n\n{markdown_list(args.completion_criterion)}\n\n"
        f"## Coordination justification\n\n{coordination.strip()}\n"
    )


def command_add_worker(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    runtime = runtime_dir(root)
    assert_valid(runtime)
    if not WORKER_ID_RE.fullmatch(args.worker_id):
        raise StateError("worker-id must match worker-N with N greater than zero")
    objective = require_nonempty(args.objective, "objective")
    scopes = [require_nonempty(item, "allowed-scope") for item in args.allowed_scope]
    criteria = [
        require_nonempty(item, "completion-criterion") for item in args.completion_criterion
    ]
    state = load_state(runtime)
    registry = state["workers"]
    if state["status"] == "complete":
        raise StateError("Cannot add a Worker to a completed project")
    if any(item["id"] == args.worker_id for item in registry):
        raise StateError(f"Worker already exists: {args.worker_id}")
    known_ids = {item["id"] for item in registry}
    unknown = sorted(set(args.depends_on) - known_ids)
    if unknown:
        raise StateError(f"Unknown Worker dependencies: {', '.join(unknown)}")
    if len(registry) >= 3 and not (args.coordination_justification or "").strip():
        raise StateError("More than three Workers requires --coordination-justification")
    for item in registry:
        overlap = sorted(set(scopes) & set(item["write_scope"]))
        if overlap:
            raise StateError(
                f"Write scope overlaps with {item['id']}: {', '.join(overlap)}"
            )

    args.objective = objective
    worker_dir = runtime / "workers" / args.worker_id
    if worker_dir.exists():
        raise StateError(f"Refusing to overwrite existing Worker directory: {worker_dir}")
    worker_dir.mkdir(parents=True)
    try:
        write_new_text(worker_dir / "TASK.md", build_worker_task(args))
        status = read_template_json("worker-status.json")
        status["worker_id"] = args.worker_id
        status["last_updated"] = utc_now()
        write_new_json(worker_dir / "STATUS.json", status)
        write_new_text(worker_dir / "BLOCKER.md", read_template_text("blocker.md"))
    except Exception:
        for child in worker_dir.iterdir():
            child.unlink()
        worker_dir.rmdir()
        raise

    registry.append(
        {
            "id": args.worker_id,
            "task_path": f"workers/{args.worker_id}/TASK.md",
            "status_path": f"workers/{args.worker_id}/STATUS.json",
            "write_scope": scopes,
            "depends_on": list(args.depends_on),
        }
    )
    state["next_action"] = {
        "actor": "project-lead",
        "instruction": "Finish assignments, then move the project to execution.",
    }
    save_state(runtime, state)
    assert_valid(runtime)
    print(f"Registered {args.worker_id}")
    return 0


WORKER_TRANSITIONS = {
    "ready": {"active", "blocked", "waiting-owner", "completed", "inactive"},
    "active": {"blocked", "waiting-owner", "completed", "inactive"},
    "blocked": {"active", "waiting-owner", "inactive"},
    "waiting-owner": {"active", "blocked", "inactive"},
    "completed": {"inactive"},
    "inactive": {"ready", "active"},
}


def command_set_worker_status(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    runtime = runtime_dir(root)
    assert_valid(runtime)
    state = load_state(runtime)
    registry = {item["id"]: item for item in state["workers"]}
    if args.worker_id not in registry:
        raise StateError(f"Unknown Worker: {args.worker_id}")
    status_path_value = checked_relative_path(
        runtime, registry[args.worker_id]["status_path"], "worker.status_path"
    )
    status = read_json(status_path_value)
    old_status = status["status"]
    if args.status != old_status and args.status not in WORKER_TRANSITIONS[old_status]:
        raise StateError(f"Invalid Worker transition: {old_status} -> {args.status}")
    if args.status == "active" and old_status != "active":
        for dependency in registry[args.worker_id]["depends_on"]:
            dependency_status_path = checked_relative_path(
                runtime, registry[dependency]["status_path"], "dependency.status_path"
            )
            dependency_status = read_json(dependency_status_path)["status"]
            if dependency_status not in {"completed", "inactive"}:
                raise StateError(
                    f"Cannot activate {args.worker_id}; dependency {dependency} "
                    f"is {dependency_status}"
                )
    status["status"] = args.status
    status["summary"] = require_nonempty(args.summary, "summary")
    status["next_action"] = args.next_action.strip()
    if args.files_changed is not None:
        status["files_changed"] = args.files_changed
    if args.verification is not None:
        status["verification"] = args.verification
    status["last_updated"] = utc_now()
    atomic_write_json(status_path_value, status)
    assert_valid(runtime)
    print(f"Updated {args.worker_id}: {old_status} -> {args.status}")
    return 0


PHASE_TRANSITIONS = {
    "planning": {"planning", "execution", "complete"},
    "execution": {"execution", "planning", "review", "complete"},
    "review": {"review", "execution", "complete"},
    "complete": {"complete"},
}
PROJECT_STATUS_TRANSITIONS = {
    "active": {"active", "blocked", "waiting-owner", "complete"},
    "blocked": {"active", "blocked", "waiting-owner", "complete"},
    "waiting-owner": {"active", "blocked", "waiting-owner", "complete"},
    "complete": {"complete"},
}


def command_set_project(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    runtime = runtime_dir(root)
    assert_valid(runtime)
    state = load_state(runtime)
    phase = args.phase or state["phase"]
    status = args.status or state["status"]
    if phase not in PHASE_TRANSITIONS[state["phase"]]:
        raise StateError(f"Invalid project phase transition: {state['phase']} -> {phase}")
    if status not in PROJECT_STATUS_TRANSITIONS[state["status"]]:
        raise StateError(f"Invalid project status transition: {state['status']} -> {status}")
    if (phase == "complete") != (status == "complete"):
        raise StateError("phase and status must both be complete or both be non-complete")
    state["phase"] = phase
    state["status"] = status
    if args.milestone:
        state["current_milestone"] = require_nonempty(args.milestone, "milestone")
    if args.next_actor or args.next_action:
        if not (args.next_actor and args.next_action):
            raise StateError("--next-actor and --next-action must be supplied together")
        state["next_action"] = {
            "actor": require_nonempty(args.next_actor, "next-actor"),
            "instruction": require_nonempty(args.next_action, "next-action"),
        }
    save_state(runtime, state)
    assert_valid(runtime)
    print(f"Project is {phase}/{status}")
    return 0


def command_assign_review(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    runtime = runtime_dir(root)
    assert_valid(runtime)
    if not REVIEWER_ID_RE.fullmatch(args.reviewer_id):
        raise StateError("reviewer-id must match reviewer-N with N greater than zero")
    if args.level not in {"balanced", "strong"}:
        raise StateError("Review level must be balanced or strong")
    state = load_state(runtime)
    if state["status"] == "complete":
        raise StateError("Cannot assign review to a completed project")
    current_status = read_json(runtime / "review" / "STATUS.json")
    if state["review"]["required"] and current_status["status"] not in {
        "completed",
        "not-requested",
    }:
        raise StateError("A review assignment is already active")
    task = (
        f"# Review Task: {args.reviewer_id}\n\n"
        f"## Objective\n\n{require_nonempty(args.objective, 'objective')}\n\n"
        f"## Review level\n\n{args.level}\n\n"
        f"## Scope\n\n{markdown_list(args.scope)}\n\n"
        f"## Completion criteria\n\n{markdown_list(args.completion_criterion)}\n"
    )
    atomic_write_text(runtime / "review" / "TASK.md", task)
    atomic_write_text(runtime / "review" / "REPORT.md", read_template_text("review-report.md"))
    review_status = read_template_json("review-status.json")
    review_status.update(
        {
            "reviewer_id": args.reviewer_id,
            "status": "ready",
            "summary": "Review assignment is ready.",
            "last_updated": utc_now(),
        }
    )
    atomic_write_json(runtime / "review" / "STATUS.json", review_status)
    state["review"].update(
        {
            "required": True,
            "level": args.level,
            "reviewer_id": args.reviewer_id,
        }
    )
    state["phase"] = "review"
    state["status"] = "active"
    state["next_action"] = {
        "actor": args.reviewer_id,
        "instruction": f"Continue {args.reviewer_id} and complete the assigned review.",
    }
    save_state(runtime, state)
    assert_valid(runtime)
    print(f"Assigned {args.reviewer_id} ({args.level})")
    return 0


REVIEW_TRANSITIONS = {
    "not-requested": {"ready"},
    "ready": {"active", "blocked", "completed"},
    "active": {"blocked", "completed"},
    "blocked": {"active", "completed"},
    "completed": {"ready"},
}


def command_set_review_status(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    runtime = runtime_dir(root)
    assert_valid(runtime)
    path = runtime / "review" / "STATUS.json"
    status = read_json(path)
    if status["reviewer_id"] != args.reviewer_id:
        raise StateError("Reviewer ID does not match the active assignment")
    old_status = status["status"]
    if args.status != old_status and args.status not in REVIEW_TRANSITIONS[old_status]:
        raise StateError(f"Invalid review transition: {old_status} -> {args.status}")
    status["status"] = args.status
    status["summary"] = require_nonempty(args.summary, "summary")
    if args.verification is not None:
        status["verification"] = args.verification
    status["last_updated"] = utc_now()
    atomic_write_json(path, status)
    assert_valid(runtime)
    print(f"Updated review: {old_status} -> {args.status}")
    return 0


def command_record_owner_feedback(args: argparse.Namespace) -> int:
    root = project_root(args.project_root)
    runtime = runtime_dir(root)
    assert_valid(runtime)
    if not WORKER_ID_RE.fullmatch(args.worker_id):
        raise StateError("worker-id must match worker-N")
    state = load_state(runtime)
    if args.worker_id not in {item["id"] for item in state["workers"]}:
        raise StateError(f"Unknown Worker: {args.worker_id}")
    message = require_nonempty(args.message, "message")
    now = utc_now()
    event_id = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + f"-{args.worker_id}-"
        + uuid.uuid4().hex[:8]
    )
    content = read_template_text("owner-feedback.md")
    replacements = {
        "{{EVENT_ID}}": event_id,
        "{{WORKER_ID}}": args.worker_id,
        "{{CREATED_AT}}": now,
        "{{RAW_MESSAGE}}": message,
    }
    for old, new in replacements.items():
        content = content.replace(old, new)
    path = runtime / "inbox" / "owner" / f"{event_id}.md"
    write_new_text(path, content)
    print(path)
    return 0


def pending_owner_events(runtime: Path) -> list[Path]:
    result: list[Path] = []
    for path in sorted((runtime / "inbox" / "owner").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?m)^status:\s*[\"']?pending[\"']?\s*$", text):
            result.append(path)
    return result


def status_snapshot(runtime: Path) -> dict[str, Any]:
    assert_valid(runtime)
    state = load_state(runtime)
    workers: list[dict[str, Any]] = []
    for registry in state["workers"]:
        path = checked_relative_path(runtime, registry["status_path"], "worker.status_path")
        status = read_json(path)
        workers.append(
            {
                "id": registry["id"],
                "status": status["status"],
                "summary": status["summary"],
                "verification": status["verification"],
                "next_action": status["next_action"],
            }
        )
    review_status = read_json(runtime / "review" / "STATUS.json")
    return {
        "project_id": state["project_id"],
        "phase": state["phase"],
        "status": state["status"],
        "current_milestone": state["current_milestone"],
        "workers": workers,
        "review": {
            "required": state["review"]["required"],
            "level": state["review"]["level"],
            "reviewer_id": review_status["reviewer_id"],
            "status": review_status["status"],
            "summary": review_status["summary"],
        },
        "pending_owner_feedback": len(pending_owner_events(runtime)),
        "next_action": state["next_action"],
        "last_updated": state["last_updated"],
    }


def render_status(snapshot: dict[str, Any]) -> str:
    lines = [
        f"Project: {snapshot['project_id']}",
        f"State: {snapshot['phase']} / {snapshot['status']}",
        f"Milestone: {snapshot['current_milestone']}",
        "Workers:",
    ]
    if snapshot["workers"]:
        for worker in snapshot["workers"]:
            summary = worker["summary"] or "No summary yet."
            lines.append(f"- {worker['id']}: {worker['status']} — {summary}")
    else:
        lines.append("- None registered.")
    review = snapshot["review"]
    lines.append(
        "Review: "
        + (
            f"{review['status']} ({review['level']}, {review['reviewer_id']}) — "
            f"{review['summary'] or 'No summary yet.'}"
            if review["required"]
            else "not requested"
        )
    )
    lines.append(f"Pending Owner feedback: {snapshot['pending_owner_feedback']}")
    next_action = snapshot["next_action"]
    lines.append(f"Next: {next_action['actor']} — {next_action['instruction']}")
    return "\n".join(lines)


def command_validate(args: argparse.Namespace) -> int:
    runtime = runtime_dir(project_root(args.project_root))
    errors = validate_runtime(runtime)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Valid runtime: {runtime}")
    return 0


def command_status(args: argparse.Namespace) -> int:
    runtime = runtime_dir(project_root(args.project_root))
    snapshot = status_snapshot(runtime)
    if args.json:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        print(render_status(snapshot))
    return 0


def common_project_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", default=".", help="Repository root (default: current directory)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create, validate, and summarize tiered-agent runtime state."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize .tiered-agent without overwriting")
    common_project_root(init_parser)
    init_parser.add_argument("--project-id", required=True)
    init_parser.add_argument("--profile", default="generic")
    init_parser.set_defaults(func=command_init)

    add_parser = subparsers.add_parser("add-worker", help="Register a bounded Worker assignment")
    common_project_root(add_parser)
    add_parser.add_argument("--worker-id", required=True)
    add_parser.add_argument("--objective", required=True)
    add_parser.add_argument("--allowed-scope", action="append", required=True)
    add_parser.add_argument("--read-dependency", action="append", default=[])
    add_parser.add_argument("--do-not-modify", action="append", default=[])
    add_parser.add_argument("--depends-on", action="append", default=[])
    add_parser.add_argument("--plan-section", action="append", default=[])
    add_parser.add_argument("--completion-criterion", action="append", required=True)
    add_parser.add_argument("--coordination-justification")
    add_parser.set_defaults(func=command_add_worker)

    worker_parser = subparsers.add_parser("set-worker-status", help="Update one Worker's owned status")
    common_project_root(worker_parser)
    worker_parser.add_argument("--worker-id", required=True)
    worker_parser.add_argument("--status", choices=sorted(WORKER_STATUSES), required=True)
    worker_parser.add_argument("--summary", required=True)
    worker_parser.add_argument("--next-action", default="")
    worker_parser.add_argument("--files-changed", action="append")
    worker_parser.add_argument("--verification", action="append")
    worker_parser.set_defaults(func=command_set_worker_status)

    project_parser = subparsers.add_parser("set-project", help="Update Project Lead-owned global state")
    common_project_root(project_parser)
    project_parser.add_argument("--phase", choices=sorted(PHASES))
    project_parser.add_argument("--status", choices=sorted(PROJECT_STATUSES))
    project_parser.add_argument("--milestone")
    project_parser.add_argument("--next-actor")
    project_parser.add_argument("--next-action")
    project_parser.set_defaults(func=command_set_project)

    review_parser = subparsers.add_parser("assign-review", help="Create a bounded review assignment")
    common_project_root(review_parser)
    review_parser.add_argument("--reviewer-id", required=True)
    review_parser.add_argument("--level", choices=["balanced", "strong"], required=True)
    review_parser.add_argument("--objective", required=True)
    review_parser.add_argument("--scope", action="append", default=[])
    review_parser.add_argument("--completion-criterion", action="append", required=True)
    review_parser.set_defaults(func=command_assign_review)

    review_status_parser = subparsers.add_parser("set-review-status", help="Update Reviewer-owned status")
    common_project_root(review_status_parser)
    review_status_parser.add_argument("--reviewer-id", required=True)
    review_status_parser.add_argument("--status", choices=sorted(REVIEW_STATUSES), required=True)
    review_status_parser.add_argument("--summary", required=True)
    review_status_parser.add_argument("--verification", action="append")
    review_status_parser.set_defaults(func=command_set_review_status)

    feedback_parser = subparsers.add_parser(
        "record-owner-feedback", help="Preserve ambiguous Owner feedback verbatim"
    )
    common_project_root(feedback_parser)
    feedback_parser.add_argument("--worker-id", required=True)
    feedback_parser.add_argument("--message", required=True)
    feedback_parser.set_defaults(func=command_record_owner_feedback)

    validate_parser = subparsers.add_parser("validate", help="Validate runtime structure and invariants")
    common_project_root(validate_parser)
    validate_parser.set_defaults(func=command_validate)

    status_parser = subparsers.add_parser("status", help="Render a concise management status")
    common_project_root(status_parser)
    status_parser.add_argument("--json", action="store_true", help="Emit a JSON snapshot")
    status_parser.set_defaults(func=command_status)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except StateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
