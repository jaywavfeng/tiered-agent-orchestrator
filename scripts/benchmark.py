#!/usr/bin/env python3
"""Validate and aggregate paired orchestration benchmark records."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional


STRATEGIES = {"strong-only", "tiered"}
TOKEN_KEYS = {"total", "strong", "balanced", "economy"}
NONNEGATIVE_INTEGERS = {
    "model_switches",
    "worker_threads",
    "escalations",
    "user_interventions",
}
MEASUREMENT_SOURCES = {
    "host-per-model-telemetry",
    "documented-manual-per-conversation",
}


class BenchmarkError(RuntimeError):
    pass


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as exc:
        raise BenchmarkError(f"Input does not exist: {path}") from exc
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BenchmarkError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise BenchmarkError(f"{path}:{line_number}: record must be an object")
        errors = validate_record(value)
        if errors:
            raise BenchmarkError(
                f"{path}:{line_number}: " + "; ".join(errors)
            )
        records.append(value)
    if not records:
        raise BenchmarkError(f"No benchmark records found in {path}")
    return records


def validate_record(record: dict[str, Any]) -> list[str]:
    required = {
        "schema_version",
        "task_id",
        "strategy",
        "success",
        "test_pass_rate",
        "tokens",
        "measurement_source",
        "measurement_evidence",
        "estimated_cost",
        "credits_used",
        "duration_seconds",
        "model_switches",
        "worker_threads",
        "escalations",
        "user_interventions",
        "recorded_at",
        "notes",
    }
    errors: list[str] = []
    missing = sorted(required - record.keys())
    extra = sorted(record.keys() - required)
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if extra:
        errors.append("unknown fields: " + ", ".join(extra))
    if missing:
        return errors
    if record["schema_version"] != 2:
        errors.append("schema_version must be 2")
    if not isinstance(record["task_id"], str) or not record["task_id"].strip():
        errors.append("task_id must be a non-empty string")
    if record["strategy"] not in STRATEGIES:
        errors.append("strategy must be strong-only or tiered")
    if not isinstance(record["success"], bool):
        errors.append("success must be boolean")
    rate = record["test_pass_rate"]
    if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not 0 <= rate <= 1:
        errors.append("test_pass_rate must be between 0 and 1")

    tokens = record["tokens"]
    if not isinstance(tokens, dict) or set(tokens) != TOKEN_KEYS:
        errors.append("tokens must contain exactly total, strong, balanced, and economy")
    else:
        for key, value in tokens.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"tokens.{key} must be a non-negative integer")
        if not errors and tokens["total"] != (
            tokens["strong"] + tokens["balanced"] + tokens["economy"]
        ):
            errors.append("tokens.total must equal the three tier totals")

    cost = record["estimated_cost"]
    if cost is not None and (
        isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost < 0
    ):
        errors.append("estimated_cost must be null or a non-negative number")
    credits = record["credits_used"]
    if credits is not None and (
        isinstance(credits, bool) or not isinstance(credits, (int, float)) or credits < 0
    ):
        errors.append("credits_used must be null or a non-negative number")
    if not isinstance(record["measurement_source"], str) or record[
        "measurement_source"
    ] not in MEASUREMENT_SOURCES:
        errors.append("measurement_source must identify attributable host or manual telemetry")
    if not isinstance(record["measurement_evidence"], str) or not record[
        "measurement_evidence"
    ].strip():
        errors.append("measurement_evidence must be a non-empty string")
    duration = record["duration_seconds"]
    if isinstance(duration, bool) or not isinstance(duration, (int, float)) or duration < 0:
        errors.append("duration_seconds must be a non-negative number")
    for key in NONNEGATIVE_INTEGERS:
        value = record[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(f"{key} must be a non-negative integer")
    for key in ("recorded_at", "notes"):
        if not isinstance(record[key], str):
            errors.append(f"{key} must be a string")
    return errors


def mean(records: list[dict[str, Any]], getter) -> float:
    return float(statistics.fmean(getter(record) for record in records))


def strategy_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    costs = [record["estimated_cost"] for record in records if record["estimated_cost"] is not None]
    credits = [record["credits_used"] for record in records if record["credits_used"] is not None]
    return {
        "runs": len(records),
        "success_rate": mean(records, lambda item: 1.0 if item["success"] else 0.0),
        "test_pass_rate": mean(records, lambda item: item["test_pass_rate"]),
        "tokens": {
            key: mean(records, lambda item, token_key=key: item["tokens"][token_key])
            for key in sorted(TOKEN_KEYS)
        },
        "estimated_cost": float(statistics.fmean(costs)) if costs else None,
        "credits_used": float(statistics.fmean(credits)) if credits else None,
        "duration_seconds": mean(records, lambda item: item["duration_seconds"]),
        "model_switches": mean(records, lambda item: item["model_switches"]),
        "worker_threads": mean(records, lambda item: item["worker_threads"]),
        "escalations": mean(records, lambda item: item["escalations"]),
        "user_interventions": mean(records, lambda item: item["user_interventions"]),
    }


def aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for record in records:
        grouped[record["task_id"]][record["strategy"]].append(record)
    paired_task_ids = sorted(
        task_id for task_id, strategies in grouped.items() if STRATEGIES <= strategies.keys()
    )
    if not paired_task_ids:
        raise BenchmarkError(
            "No paired task IDs: each compared task needs strong-only and tiered records"
        )
    paired_records = {
        strategy: [
            record
            for task_id in paired_task_ids
            for record in grouped[task_id][strategy]
        ]
        for strategy in sorted(STRATEGIES)
    }
    summaries = {
        strategy: strategy_summary(strategy_records)
        for strategy, strategy_records in paired_records.items()
    }
    baseline = summaries["strong-only"]
    tiered = summaries["tiered"]
    baseline_strong = baseline["tokens"]["strong"]
    reduction = (
        1.0 - tiered["tokens"]["strong"] / baseline_strong
        if baseline_strong > 0
        else None
    )
    return {
        "schema_version": 2,
        "paired_task_ids": paired_task_ids,
        "strategies": summaries,
        "delta_tiered_minus_strong_only": {
            "success_rate": tiered["success_rate"] - baseline["success_rate"],
            "test_pass_rate": tiered["test_pass_rate"] - baseline["test_pass_rate"],
            "total_tokens": tiered["tokens"]["total"] - baseline["tokens"]["total"],
            "strong_tokens": tiered["tokens"]["strong"] - baseline["tokens"]["strong"],
            "duration_seconds": tiered["duration_seconds"] - baseline["duration_seconds"],
            "credits_used": (
                tiered["credits_used"] - baseline["credits_used"]
                if tiered["credits_used"] is not None and baseline["credits_used"] is not None
                else None
            ),
            "model_switches": tiered["model_switches"] - baseline["model_switches"],
            "user_interventions": tiered["user_interventions"] - baseline["user_interventions"],
            "strong_token_reduction_ratio": reduction,
        },
    }


def command_validate(args: argparse.Namespace) -> int:
    records = read_records(Path(args.input))
    print(f"Valid benchmark records: {len(records)}")
    return 0


def command_aggregate(args: argparse.Namespace) -> int:
    records = read_records(Path(args.input))
    result = json.dumps(aggregate(records), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(result)
        print(f"Wrote {output}")
    else:
        print(result, end="")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and aggregate paired benchmark JSONL.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("input")
    validate_parser.set_defaults(func=command_validate)
    aggregate_parser = subparsers.add_parser("aggregate")
    aggregate_parser.add_argument("input")
    aggregate_parser.add_argument("--output")
    aggregate_parser.set_defaults(func=command_aggregate)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except BenchmarkError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
