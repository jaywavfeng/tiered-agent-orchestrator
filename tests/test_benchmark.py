from __future__ import annotations

import json
import contextlib
import io
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
    def test_cli_help_exits_successfully(self):
        for args in (["--help"], ["overhead", "--help"]):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(SystemExit) as result:
                    benchmark.main(args)
            self.assertEqual(result.exception.code, 0)
            self.assertIn("usage:", output.getvalue())

    def purpose_record(self, coordination=10, task=100, unclassified=0, synthetic=False):
        value = record("purpose-fixture", "tiered", coordination, task + unclassified)
        value["purpose_usage"] = {
            "coordination": coordination, "task": task, "unclassified": unclassified,
            "source": "documented-purpose-attribution", "evidence": "Unit test attribution fixture",
            "synthetic": synthetic,
        }
        return value

    def test_overhead_ten_percent_boundary_and_excess(self):
        for coordination, expected in ((9, True), (10, True), (11, False)):
            value = self.purpose_record(coordination)
            self.assertEqual(benchmark.validate_record(value), [])
            result = benchmark.overhead_result(value)
            self.assertEqual(result["within_target"], expected)
            self.assertEqual(result["ratio"], coordination / 100)

    def test_overhead_is_unmeasured_for_missing_incomplete_or_zero_denominator(self):
        values = [record("legacy", "tiered", 10, 100), self.purpose_record(task=0),
                  self.purpose_record(unclassified=1)]
        failed = self.purpose_record()
        failed["success"] = False
        for value in [*values, failed]:
            self.assertEqual(benchmark.validate_record(value), [])
            result = benchmark.overhead_result(value)
            self.assertEqual(result["status"], "unmeasured")
            self.assertIsNone(result["ratio"])
            self.assertIsNone(result["within_target"])

    def test_synthetic_purpose_data_never_establishes_measured_savings(self):
        result = benchmark.overhead_result(self.purpose_record(synthetic=True))
        self.assertEqual(result["status"], "synthetic")
        self.assertIsNone(result["within_target"])
        self.assertIsNone(result["ratio"])

    def test_purpose_validation_rejects_unattributed_and_inconsistent_counts(self):
        for field, invalid in (("coordination", -1), ("task", True), ("unclassified", 3),
                               ("source", "host-per-model-telemetry"), ("evidence", ""), ("synthetic", "false")):
            value = self.purpose_record()
            value["purpose_usage"][field] = invalid
            self.assertTrue(benchmark.validate_record(value), (field, invalid))

    def test_aggregate_does_not_hide_an_over_budget_run_in_average(self):
        baseline = self.purpose_record()
        baseline["strategy"] = "strong-only"
        excess = self.purpose_record(50)
        result = benchmark.aggregate([baseline, self.purpose_record(0), excess])
        self.assertEqual([r["within_target"] for r in result["overhead_by_run"]], [True, True, False])

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
