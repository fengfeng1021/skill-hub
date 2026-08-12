#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("agent_skill_bridge.py")


class AgentSkillBridgeTests(unittest.TestCase):
    def test_lists_loads_and_reads_without_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "sample"
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: sample\ndescription: Use for sample work.\n---\n\n# Sample\n",
                encoding="utf-8",
            )
            (skill / "references" / "guide.md").write_text("guide\n", encoding="utf-8")

            listed = subprocess.run(
                [sys.executable, str(SCRIPT), "--skills-root", str(root), "list"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, listed.returncode, listed.stdout + listed.stderr)
            self.assertEqual("sample", json.loads(listed.stdout)[0]["name"])

            loaded = subprocess.run(
                [sys.executable, str(SCRIPT), "--skills-root", str(root), "load", "sample"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, loaded.returncode)
            self.assertIn("# Sample", json.loads(loaded.stdout)["body"])

            read = subprocess.run(
                [sys.executable, str(SCRIPT), "--skills-root", str(root), "read", "sample", "references/guide.md"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(0, read.returncode)
            self.assertEqual("guide", read.stdout.strip())

            escaped = subprocess.run(
                [sys.executable, str(SCRIPT), "--skills-root", str(root), "read", "sample", "../secret"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(2, escaped.returncode)


if __name__ == "__main__":
    unittest.main()
