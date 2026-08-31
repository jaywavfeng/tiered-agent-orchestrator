from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def test_skill_frontmatter_and_budget(self) -> None:
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertIn("name: tao", frontmatter)
        self.assertIn('version: "0.3.1"', frontmatter)
        description = re.search(r"(?m)^description:\s*(.+)$", frontmatter).group(1)
        self.assertLessEqual(len(description), 1024)
        self.assertIn("large", description)
        self.assertIn("Do not", description)
        self.assertLess(len(text.splitlines()), 500)
        self.assertLess(len(text.split()), 5000)

    def test_core_protocol_is_model_agnostic(self) -> None:
        core_paths = [ROOT / "SKILL.md", *sorted((ROOT / "references").glob("*.md"))]
        combined = "\n".join(path.read_text(encoding="utf-8") for path in core_paths)
        for model_name in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
            self.assertNotIn(model_name, combined.lower())
        for tier in ("strong", "balanced", "economy"):
            self.assertIn(tier, combined)

    def test_openai_metadata_is_discoverable(self) -> None:
        text = (ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn('display_name: "Tiered Agent Orchestrator"', text)
        self.assertIn("$tao", text)
        self.assertIn("allow_implicit_invocation: false", text)
        self.assertNotIn("dependencies:", text)

        short_description = re.search(
            r'(?m)^\s+short_description:\s+"([^"]+)"$', text
        )
        self.assertIsNotNone(short_description)
        self.assertGreaterEqual(len(short_description.group(1)), 25)
        self.assertLessEqual(len(short_description.group(1)), 64)
        default_prompt = re.search(r'(?m)^\s+default_prompt:\s+"([^"]+)"$', text)
        self.assertIsNotNone(default_prompt)
        self.assertTrue(default_prompt.group(1).startswith("$tao"))
        self.assertIn("gpt-5.6-sol", default_prompt.group(1))
        self.assertIn("gpt-5.6-luna", default_prompt.group(1))
        self.assertIn("xhigh", default_prompt.group(1))
        self.assertIn("Terra", default_prompt.group(1))
        self.assertIn("passive", default_prompt.group(1))
        self.assertRegex(text, r'(?m)^\s+allow_implicit_invocation:\s+false\s*$')

    def test_all_json_assets_and_schemas_parse(self) -> None:
        paths = [
            *sorted((ROOT / "assets").rglob("*.json")),
            *sorted((ROOT / "schemas").glob("*.json")),
            ROOT / "evals" / "evals.json",
        ]
        self.assertGreaterEqual(len(paths), 8)
        for path in paths:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))

    def test_eval_suite_covers_a_through_j(self) -> None:
        value = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
        self.assertEqual(value["skill_name"], "tao")
        ids = [item["id"] for item in value["evals"]]
        self.assertEqual(ids, list("ABCDEFGHIJ"))
        for item in value["evals"]:
            self.assertTrue(item["prompt"].strip())
            self.assertTrue(item["expected_output"].strip())
            self.assertGreaterEqual(len(item["assertions"]), 2)

    def test_readmes_share_public_contract(self) -> None:
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        shared = [
            "$tao continue worker-1",
            "$tao continue worker-2",
            "$tao status",
            "python scripts/statectl.py",
            "reassign-worker",
            "Benchmark pending",
            "Apache-2.0",
        ]
        for marker in shared:
            self.assertIn(marker, english)
            self.assertIn(marker, chinese)
        self.assertIn("You never need to copy the previous conversation.", english)
        self.assertIn("你不需要复制任何上一段聊天内容。", chinese)
        self.assertIn("README.zh-CN.md", english)
        self.assertIn("README.md", chinese)

    def test_worker_identity_is_reusable_across_assignments(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        protocol = (ROOT / "references" / "orchestration-protocol.md").read_text(
            encoding="utf-8"
        )
        runtime = (ROOT / "references" / "runtime-state.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("long-lived role and conversation, not a single task", skill)
        self.assertIn("Completing M1 does not justify creating `worker-2`", protocol)
        self.assertIn("completed → ready", runtime)
        self.assertIn("history/assignment-", runtime)
        self.assertIn("Only PROJECT_LEAD", protocol)

    def test_cost_first_dispatch_contract_is_hard(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        protocol = (ROOT / "references" / "orchestration-protocol.md").read_text(
            encoding="utf-8"
        )
        profile = (ROOT / "profiles" / "openai-codex.md").read_text(encoding="utf-8")
        for text in (skill, protocol):
            self.assertIn("MUST NOT", text)
            self.assertIn("poll", text.lower())
            self.assertIn("economy model", text.lower())
        self.assertIn('model: "gpt-5.6-luna"', profile)
        self.assertIn("MUST NOT be omitted", profile)
        self.assertIn("MUST NOT spawn", profile)
        self.assertIn('reasoning_effort: "xhigh"', profile)
        self.assertIn("gpt-5.6-luna / xhigh", profile)

    def test_completion_value_routing_and_escalation_contract(self) -> None:
        principle = "Use the cheapest model that is likely to complete the task correctly without costly rework."
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        protocol = (ROOT / "references" / "orchestration-protocol.md").read_text(
            encoding="utf-8"
        )
        profile = (ROOT / "profiles" / "openai-codex.md").read_text(encoding="utf-8")
        for text in (skill, protocol, profile):
            self.assertIn(principle, text)
        self.assertIn("gpt-5.6-luna", profile)
        self.assertIn("Extra High (`xhigh`)", profile)
        self.assertIn("gpt-5.6-terra", profile)
        self.assertIn("First escalation", profile)
        self.assertIn("SOL escalation", profile)
        self.assertIn("Terra remains insufficient", profile)

    def test_native_dispatch_verifies_effective_runtime_and_waits_by_event(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        protocol = (ROOT / "references" / "orchestration-protocol.md").read_text(
            encoding="utf-8"
        ).lower()
        runtime = (ROOT / "references" / "runtime-state.md").read_text(
            encoding="utf-8"
        ).lower()
        for text in (skill, protocol, runtime):
            self.assertIn("actual/effective runtime model", text)
            self.assertIn("nickname", text)
            self.assertIn("unconfirmed", text)
            self.assertIn("passive", text)
            self.assertIn("timeout is not a milestone", text)
        self.assertIn("same failure", skill)
        self.assertIn("same failure", protocol)

    def test_lead_delegates_mechanical_work(self) -> None:
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8").lower()
        protocol = (ROOT / "references" / "orchestration-protocol.md").read_text(
            encoding="utf-8"
        ).lower()
        for text in (skill, protocol):
            self.assertIn("ssh", text)
            self.assertIn("nvidia-smi", text)
            self.assertIn("must not", text)
            self.assertIn("strong reasoning", text)

    def test_readmes_document_model_fallback_and_event_handoff(self) -> None:
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text(encoding="utf-8").lower()
            with self.subTest(name=name):
                self.assertIn("gpt-5.6-luna", text)
                self.assertIn("status.json", text)
                self.assertTrue("poll" in text or "轮询" in text)
                self.assertIn("worker-1", text)

    def test_readmes_show_automatic_and_manual_economy_flows(self) -> None:
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("explicit spawn of gpt-5.6-luna / xhigh worker-1", english)
        self.assertIn("Owner opens gpt-5.6-luna / xhigh", english)
        self.assertIn("silently inherits Sol", english)
        self.assertIn("显式 spawn gpt-5.6-luna / xhigh worker-1", chinese)
        self.assertIn("Owner 打开 gpt-5.6-luna / xhigh", chinese)
        self.assertIn("继承 Sol", chinese)

    def test_legacy_invocation_name_is_absent(self) -> None:
        legacy = "$tiered-agent-" + "orchestrator"
        text_suffixes = {".json", ".md", ".py", ".yaml", ".yml"}
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.suffix not in text_suffixes or ".git" in path.parts:
                continue
            with self.subTest(path=path):
                self.assertNotIn(legacy, path.read_text(encoding="utf-8"))

    def test_local_markdown_links_resolve(self) -> None:
        markdown_files = [
            ROOT / "SKILL.md",
            ROOT / "README.md",
            ROOT / "README.zh-CN.md",
            *sorted((ROOT / "references").glob("*.md")),
            *sorted((ROOT / "profiles").glob("*.md")),
            *sorted((ROOT / "benchmarks").glob("*.md")),
            *sorted((ROOT / "examples").glob("*.md")),
        ]
        pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for source in markdown_files:
            for target in pattern.findall(source.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                path_part = target.split("#", 1)[0]
                resolved = (source.parent / path_part).resolve()
                with self.subTest(source=source, target=target):
                    self.assertTrue(resolved.exists(), f"Broken local link: {source} -> {target}")


if __name__ == "__main__":
    unittest.main()
