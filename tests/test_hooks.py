"""Behavior of hooks/agentfleex.py on small repositories."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve().parent.parent / "hooks/agentfleex.py"


class HooksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.data = Path(self.tmp.name) / "data"
        self.bin = Path(self.tmp.name) / "bin"
        self.root.mkdir()
        self.bin.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.write("notes.txt", "one\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "init")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.root, check=True)

    def write(self, name: str, text: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Bytes keep LF line endings on Windows too.
        path.write_bytes(text.encode("utf-8"))

    def hook(self, name: str, **event: Any) -> dict[str, Any]:
        event = {"session_id": "s1", "cwd": str(self.root), **event}
        path = f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), name],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PATH": path, "CLAUDE_PLUGIN_DATA": str(self.data)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        reply: dict[str, Any] = json.loads(result.stdout)
        return reply

    def test_stop_without_changes_allows(self) -> None:
        self.assertEqual(self.hook("stop"), {})

    def test_stop_blocks_once_per_state(self) -> None:
        self.write("notes.txt", "one \n")
        reply = self.hook("stop")
        self.assertEqual(reply["decision"], "block")
        self.assertIn("git whitespace failed", reply["reason"])
        self.assertIn("editor diagnostics", reply["reason"])
        self.assertEqual(self.hook("stop"), {})
        self.assertEqual(self.hook("stop", stop_hook_active=True), {})

    def test_stop_hook_active_allows(self) -> None:
        self.write("notes.txt", "one \n")
        self.assertEqual(self.hook("stop", stop_hook_active=True), {})

    def fake_yamllint(self) -> None:
        self.write(".yamllint", "extends: default\n")
        self.write("old.yml", "a: 1\n")
        self.git("add", ".")
        self.git("commit", "-q", "-m", "yaml")
        if os.name == "nt":
            (self.bin / "yamllint.cmd").write_text("@echo checked %*\r\n@exit /b 1\r\n")
        else:
            fake = self.bin / "yamllint"
            fake.write_text('#!/bin/sh\necho "checked $*"\nexit 1\n')
            fake.chmod(0o755)
        self.write("new.yml", "b: 2\n")
        self.write("notes.txt", "two\n")

    def consent(self, answer: str) -> None:
        subprocess.run(
            [sys.executable, str(SCRIPT), "consent", answer, str(self.root)],
            capture_output=True,
            check=True,
            env={
                **os.environ,
                "PATH": f"{self.bin}{os.pathsep}{os.environ.get('PATH', '')}",
                "CLAUDE_PLUGIN_DATA": str(self.data),
            },
        )

    def test_stop_asks_before_running_repository_tools(self) -> None:
        self.fake_yamllint()
        reason = self.hook("stop")["reason"]
        self.assertIn("Ask the user", reason)
        self.assertIn("consent yes", reason)
        self.assertIn("editor diagnostics", reason)
        self.assertNotIn("checked", reason)
        # Asked once per session: without an answer the tools stay off.
        self.assertEqual(self.hook("stop"), {})

    def test_stop_checks_only_changed_files_after_consent(self) -> None:
        self.fake_yamllint()
        self.consent("yes")
        reason = self.hook("stop")["reason"]
        self.assertIn("checked new.yml", reason)
        self.assertNotIn("old.yml", reason)
        self.assertNotIn("notes.txt", reason)

    def test_stop_never_runs_declined_tools(self) -> None:
        self.fake_yamllint()
        self.consent("no")
        self.assertEqual(self.hook("stop"), {})

    def test_read_outlines_long_file_once(self) -> None:
        self.write("big.py", "".join(f"def f{i}():\n    return {i}\n\n" for i in range(200)))
        reply = self.hook("read", tool_input={"file_path": "big.py"})["hookSpecificOutput"]
        self.assertEqual(reply["permissionDecision"], "deny")
        self.assertIn("function f0", reply["permissionDecisionReason"])
        self.assertEqual(self.hook("read", tool_input={"file_path": "big.py"}), {})

    def test_read_allows_ranges_and_short_files(self) -> None:
        self.write("big.py", "".join(f"def f{i}():\n    return {i}\n\n" for i in range(200)))
        self.assertEqual(self.hook("read", tool_input={"file_path": "big.py", "offset": 10}), {})
        self.assertEqual(self.hook("read", tool_input={"file_path": "notes.txt"}), {})


if __name__ == "__main__":
    unittest.main()
