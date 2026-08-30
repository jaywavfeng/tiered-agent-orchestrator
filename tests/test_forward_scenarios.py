from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATECTL = ROOT / "scripts" / "statectl.py"


class ForwardScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, expected: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, str(STATECTL), *args, "--project-root", str(self.root)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def init(self) -> Path:
        self.run_cli("init", "--project-id", "forward-test", "--profile", "generic")
        return self.root / ".tiered-agent"

    def add_worker(
        self, worker_id: str, scope: str, *extra: str
    ) -> subprocess.CompletedProcess[str]:
        return self.run_cli(
            "add-worker",
            "--worker-id",
            worker_id,
            "--objective",
            f"Implement the bounded {worker_id} deliverable.",
            "--allowed-scope",
            scope,
            "--read-dependency",
            "tests/**",
            "--do-not-modify",
            "public-api/**",
            "--completion-criterion",
            "Targeted tests pass.",
            *extra,
        )

    def test_normal_one_worker_handoff_is_self_contained(self) -> None:
        runtime = self.init()
        self.add_worker("worker-1", "src/import/**")
        self.run_cli(
            "set-project",
            "--phase",
            "execution",
            "--status",
            "active",
            "--milestone",
            "Implement import pipeline",
            "--next-actor",
            "worker-1",
            "--next-action",
            "Continue worker-1.",
        )
        self.run_cli("validate")
        task = (runtime / "workers" / "worker-1" / "TASK.md").read_text(
            encoding="utf-8"
        )
        for heading in (
            "## Objective",
            "## Allowed scope",
            "## Read dependencies",
            "## Do not modify",
            "## Completion criteria",
        ):
            self.assertIn(heading, task)
        state = json.loads((runtime / "STATE.json").read_text(encoding="utf-8"))
        self.assertNotIn("chat", json.dumps(state).lower())
        self.assertEqual(state["next_action"]["actor"], "worker-1")

    def test_blocker_and_ambiguous_feedback_preserve_evidence(self) -> None:
        runtime = self.init()
        self.add_worker("worker-1", "src/import/**")
        self.run_cli(
            "set-worker-status",
            "--worker-id",
            "worker-1",
            "--status",
            "blocked",
            "--summary",
            "Dependency API invalidates the architecture assumption.",
            "--next-action",
            "Return to the original Project Lead.",
        )
        blocker = runtime / "workers" / "worker-1" / "BLOCKER.md"
        blocker.write_text(
            "# Blocker\n\n## Evidence\nReproduction fails deterministically.\n\n"
            "## Attempts and lessons\nTwo alternatives require plan changes.\n\n"
            "## Safe state\nNo out-of-scope changes.\n\n"
            "## Decision needed\nChoose the replacement architecture.\n",
            encoding="utf-8",
        )
        message = (
            "This feels too engineered; I want it more research-oriented "
            "but not more complicated."
        )
        self.run_cli(
            "record-owner-feedback",
            "--worker-id",
            "worker-1",
            "--message",
            message,
        )
        event = next((runtime / "inbox" / "owner").glob("*.md"))
        self.assertIn(message, event.read_text(encoding="utf-8"))
        status = self.run_cli("status").stdout
        self.assertIn("worker-1: blocked", status)
        self.assertIn("Pending Owner feedback: 1", status)
        escalation = (ROOT / "references" / "escalation-and-review.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("do not need to copy any context", escalation)

    def test_fresh_worker_cannot_start_before_dependency_then_can_continue(self) -> None:
        runtime = self.init()
        self.add_worker("worker-1", "src/core/**")
        self.add_worker(
            "worker-2",
            "src/adapter/**",
            "--depends-on",
            "worker-1",
            "--coordination-justification",
            "The adapter has a distinct context and can start after the core handoff.",
        )
        blocked = self.run_cli(
            "set-worker-status",
            "--worker-id",
            "worker-2",
            "--status",
            "active",
            "--summary",
            "Attempted premature start.",
            expected=2,
        )
        self.assertIn("dependency worker-1 is ready", blocked.stderr)
        self.run_cli(
            "set-worker-status",
            "--worker-id",
            "worker-1",
            "--status",
            "completed",
            "--summary",
            "Core contract completed and verified.",
        )
        self.run_cli(
            "set-worker-status",
            "--worker-id",
            "worker-2",
            "--status",
            "active",
            "--summary",
            "Fresh conversation reconstructed the ready assignment.",
            "--next-action",
            "Implement adapter tests.",
        )
        self.run_cli("validate")
        minimal_files = [
            runtime / "STATE.json",
            runtime / "OWNER_DIRECTIVES.md",
            runtime / "workers" / "worker-2" / "TASK.md",
            runtime / "workers" / "worker-2" / "STATUS.json",
        ]
        self.assertTrue(all(path.is_file() for path in minimal_files))
        task = minimal_files[2].read_text(encoding="utf-8")
        self.assertIn("worker-1", task)
        self.assertNotIn("previous conversation", task.lower())


if __name__ == "__main__":
    unittest.main()
