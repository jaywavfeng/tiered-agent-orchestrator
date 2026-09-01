from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import benchmark  # noqa: E402


def record(task_id: str, strategy: str, strong: int, economy: int) -> dict:
    total = strong + economy
    return {
        "schema_version": 2,
        "task_id": task_id,
        "strategy": strategy,
        "success": True,
        "test_pass_rate": 1.0,
        "tokens": {
            "total": total,
            "strong": strong,
            "balanced": 0,
            "economy": economy,
        },
        "measurement_source": "documented-manual-per-conversation",
        "measurement_evidence": "Unit-test fixture with explicit per-conversation counts.",
        "estimated_cost": None,
        "credits_used": None,
        "duration_seconds": 10,
        "model_switches": 0 if strategy == "strong-only" else 1,
        "worker_threads": 0 if strategy == "strong-only" else 1,
        "escalations": 0,
        "user_interventions": 0,
        "recorded_at": "2026-08-30T00:00:00Z",
        "notes": "Synthetic unit-test record; not a published benchmark result.",
    }


class BenchmarkTests(unittest.TestCase):
    def test_record_validation_rejects_bad_total(self) -> None:
        value = record("task-a", "tiered", 100, 200)
        value["tokens"]["total"] = 1
        errors = benchmark.validate_record(value)
        self.assertIn("tokens.total must equal the three tier totals", errors)

    def test_record_requires_attributable_measurement_evidence(self) -> None:
        value = record("task-a", "tiered", 100, 200)
        value["measurement_evidence"] = ""
        errors = benchmark.validate_record(value)
        self.assertIn("measurement_evidence must be a non-empty string", errors)

    def test_aggregate_pairs_tasks_and_computes_reduction(self) -> None:
        values = [
            record("task-a", "strong-only", 1000, 0),
            record("task-a", "tiered", 200, 500),
            record("unpaired", "tiered", 5, 20),
        ]
        result = benchmark.aggregate(values)
        self.assertEqual(result["paired_task_ids"], ["task-a"])
        self.assertAlmostEqual(
            result["delta_tiered_minus_strong_only"][
                "strong_token_reduction_ratio"
            ],
            0.8,
        )
        self.assertEqual(
            result["delta_tiered_minus_strong_only"]["total_tokens"], -300
        )

    def test_jsonl_reader_requires_paired_data_only_at_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs.jsonl"
            path.write_text(
                json.dumps(record("task-a", "tiered", 10, 20)) + "\n",
                encoding="utf-8",
            )
            values = benchmark.read_records(path)
            self.assertEqual(len(values), 1)
            with self.assertRaises(benchmark.BenchmarkError):
                benchmark.aggregate(values)


if __name__ == "__main__":
    unittest.main()
