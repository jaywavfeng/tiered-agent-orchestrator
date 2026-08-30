from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import statectl  # noqa: E402


class StateCtlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = statectl.main([*args, "--project-root", str(self.root)])
        return result, stdout.getvalue(), stderr.getvalue()

    def init(self) -> Path:
        result, _, error = self.run_cli(
            "init", "--project-id", "sample-project", "--profile", "generic"
        )
        self.assertEqual(result, 0, error)
        return self.root / ".tiered-agent"

    def add_worker(
        self,
        worker_id: str = "worker-1",
        scope: str = "src/**",
        *extra: str,
    ) -> tuple[int, str, str]:
        return self.run_cli(
            "add-worker",
            "--worker-id",
            worker_id,
            "--objective",
            f"Complete {worker_id} work.",
            "--allowed-scope",
            scope,
            "--read-dependency",
            "tests/**",
            "--completion-criterion",
            "Relevant tests pass.",
            *extra,
        )

    def reassign_worker(
        self,
        worker_id: str = "worker-1",
        scope: str = "src/m2/**",
        *extra: str,
    ) -> tuple[int, str, str]:
        return self.run_cli(
            "reassign-worker",
            "--worker-id",
            worker_id,
            "--milestone",
            "M2",
            "--objective",
            "Complete the M2 assignment.",
            "--allowed-scope",
            scope,
            "--read-dependency",
            "src/m1/**",
            "--completion-criterion",
            "M2 tests pass.",
            *extra,
        )

    def test_init_is_idempotent_and_does_not_overwrite(self) -> None:
        runtime = self.init()
        before = (runtime / "STATE.json").read_bytes()
        result, output, error = self.run_cli(
            "init", "--project-id", "different-project", "--profile", "other"
        )
        self.assertEqual(result, 0, error)
        self.assertIn("Already initialized", output)
        self.assertEqual((runtime / "STATE.json").read_bytes(), before)

    def test_partial_runtime_is_rejected(self) -> None:
        (self.root / ".tiered-agent").mkdir()
        result, _, error = self.run_cli(
            "init", "--project-id", "sample-project", "--profile", "generic"
        )
        self.assertEqual(result, 2)
        self.assertIn("partial runtime", error)

    def test_worker_registration_status_and_summary(self) -> None:
        runtime = self.init()
        result, _, error = self.add_worker()
        self.assertEqual(result, 0, error)
        result, _, error = self.run_cli(
            "set-project",
            "--phase",
            "execution",
            "--status",
            "active",
            "--milestone",
            "Implement",
            "--next-actor",
            "worker-1",
            "--next-action",
            "Continue worker-1.",
        )
        self.assertEqual(result, 0, error)
        result, _, error = self.run_cli(
            "set-worker-status",
            "--worker-id",
            "worker-1",
            "--status",
            "active",
            "--summary",
            "Implementation is underway.",
            "--next-action",
            "Run tests.",
            "--files-changed",
            "src/example.py",
            "--verification",
            "unit tests pending",
        )
        self.assertEqual(result, 0, error)
        result, output, error = self.run_cli("status")
        self.assertEqual(result, 0, error)
        self.assertIn("worker-1: active", output)
        self.assertIn("Implementation is underway.", output)
        state = json.loads((runtime / "STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(state["workers"][0]["task_path"], "workers/worker-1/TASK.md")

    def test_blocker_recovery_and_completion_transitions(self) -> None:
        self.init()
        self.assertEqual(self.add_worker()[0], 0)
        self.assertEqual(
            self.run_cli(
                "set-project", "--phase", "execution", "--status", "active"
            )[0],
            0,
        )
        self.assertEqual(
            self.run_cli(
                "set-worker-status",
                "--worker-id",
                "worker-1",
                "--status",
                "blocked",
                "--summary",
                "Architecture decision required.",
                "--next-action",
                "Return to Project Lead.",
            )[0],
            0,
        )
        self.assertEqual(
            self.run_cli(
                "set-project", "--phase", "execution", "--status", "blocked"
            )[0],
            0,
        )
        self.assertEqual(
            self.run_cli(
                "set-worker-status",
                "--worker-id",
                "worker-1",
                "--status",
                "active",
                "--summary",
                "Decision received; implementation resumed.",
                "--next-action",
                "Complete validation.",
            )[0],
            0,
        )
        self.assertEqual(
            self.run_cli(
                "set-project", "--phase", "execution", "--status", "active"
            )[0],
            0,
        )
        self.assertEqual(
            self.run_cli(
                "set-worker-status",
                "--worker-id",
                "worker-1",
                "--status",
                "completed",
                "--summary",
                "Implementation and tests completed.",
            )[0],
            0,
        )
        self.assertEqual(
            self.run_cli(
                "set-project", "--phase", "complete", "--status", "complete"
            )[0],
            0,
        )
        self.assertEqual(self.run_cli("validate")[0], 0)

    def test_more_than_three_workers_requires_justification(self) -> None:
        self.init()
        for number in range(1, 4):
            extra = (
                ()
                if number == 1
                else (
                    "--coordination-justification",
                    f"module-{number} is an independent parallel adapter.",
                )
            )
            result, _, error = self.add_worker(
                f"worker-{number}", f"module-{number}/**", *extra
            )
            self.assertEqual(result, 0, error)
        result, _, error = self.add_worker("worker-4", "module-4/**")
        self.assertEqual(result, 2)
        self.assertIn("requires --coordination-justification", error)
        result, _, error = self.add_worker(
            "worker-4",
            "module-4/**",
            "--coordination-justification",
            "Four independent platform adapters can be validated separately.",
        )
        self.assertEqual(result, 0, error)

    def test_duplicate_active_write_scope_is_rejected(self) -> None:
        self.init()
        self.assertEqual(self.add_worker()[0], 0)
        result, _, error = self.add_worker("worker-2", "src/**")
        self.assertEqual(result, 2)
        self.assertIn("Write scope overlaps", error)

    def test_milestone_change_does_not_register_a_new_worker(self) -> None:
        runtime = self.init()
        self.assertEqual(self.add_worker()[0], 0)
        self.assertEqual(
            self.run_cli(
                "set-project",
                "--phase",
                "execution",
                "--status",
                "active",
                "--milestone",
                "M2",
            )[0],
            0,
        )
        state = json.loads((runtime / "STATE.json").read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in state["workers"]], ["worker-1"])

    def test_completed_worker_reassignment_archives_history_and_continues(self) -> None:
        runtime = self.init()
        self.assertEqual(self.add_worker(scope="src/m1/**")[0], 0)
        early_result, _, early_error = self.reassign_worker()
        self.assertEqual(early_result, 2)
        self.assertIn("not completed", early_error)
        self.assertFalse((runtime / "workers" / "worker-1" / "history").exists())
        blocker = runtime / "workers" / "worker-1" / "BLOCKER.md"
        blocker.write_text("# Blocker\n\nResolved M1 evidence.\n", encoding="utf-8")
        self.assertEqual(
            self.run_cli(
                "set-worker-status",
                "--worker-id",
                "worker-1",
                "--status",
                "completed",
                "--summary",
                "M1 completed.",
                "--files-changed",
                "src/m1/result.py",
                "--verification",
                "M1 tests passed.",
            )[0],
            0,
        )
        old_task = (runtime / "workers" / "worker-1" / "TASK.md").read_text(
            encoding="utf-8"
        )
        direct_result, _, direct_error = self.run_cli(
            "set-worker-status",
            "--worker-id",
            "worker-1",
            "--status",
            "ready",
            "--summary",
            "Unsafe direct restart.",
        )
        self.assertEqual(direct_result, 2)
        self.assertIn("Invalid Worker transition", direct_error)

        result, output, error = self.reassign_worker()
        self.assertEqual(result, 0, error)
        self.assertIn("completed -> ready", output)
        worker_dir = runtime / "workers" / "worker-1"
        history = worker_dir / "history" / "assignment-0001"
        self.assertEqual((history / "TASK.md").read_text(encoding="utf-8"), old_task)
        self.assertEqual(
            json.loads((history / "STATUS.json").read_text(encoding="utf-8"))["status"],
            "completed",
        )
        self.assertIn(
            "Resolved M1 evidence.",
            (history / "BLOCKER.md").read_text(encoding="utf-8"),
        )
        new_task = (worker_dir / "TASK.md").read_text(encoding="utf-8")
        self.assertIn("## Assignment revision\n\n2", new_task)
        self.assertIn("Complete the M2 assignment.", new_task)
        status = json.loads((worker_dir / "STATUS.json").read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["files_changed"], [])

        state = json.loads((runtime / "STATE.json").read_text(encoding="utf-8"))
        self.assertEqual(len(state["workers"]), 1)
        self.assertEqual(state["workers"][0]["id"], "worker-1")
        self.assertEqual(state["workers"][0]["write_scope"], ["src/m2/**"])
        self.assertEqual(state["current_milestone"], "M2")
        self.assertEqual(state["next_action"]["actor"], "worker-1")
        self.assertEqual(
            self.run_cli(
                "set-worker-status",
                "--worker-id",
                "worker-1",
                "--status",
                "active",
                "--summary",
                "M2 execution resumed in the same Worker conversation.",
            )[0],
            0,
        )
        self.assertEqual(self.run_cli("validate")[0], 0)

    def test_additional_parallel_worker_requires_justification(self) -> None:
        runtime = self.init()
        self.assertEqual(self.add_worker("worker-1", "src/core/**")[0], 0)
        result, _, error = self.add_worker("worker-2", "src/adapter/**")
        self.assertEqual(result, 2)
        self.assertIn("additional Worker requires --coordination-justification", error)
        result, _, error = self.add_worker(
            "worker-2",
            "src/adapter/**",
            "--coordination-justification",
            "The adapter is independently testable and ready in parallel.",
        )
        self.assertEqual(result, 0, error)
        self.assertEqual(
            self.run_cli(
                "set-worker-status",
                "--worker-id",
                "worker-2",
                "--status",
                "active",
                "--summary",
                "Independent adapter work started in parallel.",
            )[0],
            0,
        )
        state = json.loads((runtime / "STATE.json").read_text(encoding="utf-8"))
        self.assertEqual([item["id"] for item in state["workers"]], ["worker-1", "worker-2"])

    def test_reassignment_preserves_active_write_scope_ownership(self) -> None:
        runtime = self.init()
        self.assertEqual(self.add_worker("worker-1", "src/m1/**")[0], 0)
        self.assertEqual(
            self.run_cli(
                "set-worker-status",
                "--worker-id",
                "worker-1",
                "--status",
                "completed",
                "--summary",
                "M1 completed.",
            )[0],
            0,
        )
        self.assertEqual(
            self.add_worker(
                "worker-2",
                "src/shared/**",
                "--coordination-justification",
                "A separate active responsibility needs isolated context.",
            )[0],
            0,
        )
        result, _, error = self.reassign_worker("worker-1", "src/shared/**")
        self.assertEqual(result, 2)
        self.assertIn("Write scope overlaps with worker-2", error)
        self.assertFalse((runtime / "workers" / "worker-1" / "history").exists())

    def test_owner_feedback_is_verbatim_and_unique(self) -> None:
        runtime = self.init()
        self.assertEqual(self.add_worker()[0], 0)
        message = "This direction feels too heavy; keep the interface."
        result, first_path, error = self.run_cli(
            "record-owner-feedback",
            "--worker-id",
            "worker-1",
            "--message",
            message,
        )
        self.assertEqual(result, 0, error)
        result, second_path, error = self.run_cli(
            "record-owner-feedback",
            "--worker-id",
            "worker-1",
            "--message",
            message,
        )
        self.assertEqual(result, 0, error)
        self.assertNotEqual(first_path, second_path)
        events = list((runtime / "inbox" / "owner").glob("*.md"))
        self.assertEqual(len(events), 2)
        self.assertTrue(all(message in path.read_text(encoding="utf-8") for path in events))
        snapshot = statectl.status_snapshot(runtime)
        self.assertEqual(snapshot["pending_owner_feedback"], 2)

    def test_review_assignment_and_completion(self) -> None:
        self.init()
        result, _, error = self.run_cli(
            "assign-review",
            "--reviewer-id",
            "reviewer-1",
            "--level",
            "balanced",
            "--objective",
            "Review the bounded implementation.",
            "--scope",
            "src/**",
            "--completion-criterion",
            "Report evidence for every finding.",
        )
        self.assertEqual(result, 0, error)
        self.assertEqual(
            self.run_cli(
                "set-review-status",
                "--reviewer-id",
                "reviewer-1",
                "--status",
                "active",
                "--summary",
                "Review started.",
            )[0],
            0,
        )
        self.assertEqual(
            self.run_cli(
                "set-review-status",
                "--reviewer-id",
                "reviewer-1",
                "--status",
                "completed",
                "--summary",
                "Review completed with evidence.",
                "--verification",
                "All acceptance checks inspected.",
            )[0],
            0,
        )
        self.assertEqual(self.run_cli("validate")[0], 0)

    def test_tampered_escaping_path_fails_validation(self) -> None:
        runtime = self.init()
        self.assertEqual(self.add_worker()[0], 0)
        state = json.loads((runtime / "STATE.json").read_text(encoding="utf-8"))
        state["workers"][0]["task_path"] = "../outside.md"
        with (runtime / "STATE.json").open(
            "w", encoding="utf-8", newline="\n"
        ) as handle:
            handle.write(json.dumps(state))
        result, _, error = self.run_cli("validate")
        self.assertEqual(result, 1)
        self.assertIn("normalized path", error)


if __name__ == "__main__":
    unittest.main()
