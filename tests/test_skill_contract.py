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
        self.assertIn("name: tiered-agent-orchestrator", frontmatter)
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
        self.assertIn("$tiered-agent-orchestrator", text)
        self.assertIn("allow_implicit_invocation: true", text)
        self.assertNotIn("dependencies:", text)

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
            "$tiered-agent-orchestrator continue worker-1",
            "$tiered-agent-orchestrator status",
            "python scripts/statectl.py",
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
