"""Behavior of hooks/agentfleex.py on small repositories."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

SCRIPT = Path(__file__).resolve().parent.parent / "hooks/agentfleex.py"


class HooksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.data = Path(self.tmp.name) / "data"
        self.root.mkdir()
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
        result = subprocess.run(
            [sys.executable, str(SCRIPT), name],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "CLAUDE_PLUGIN_DATA": str(self.data)},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        reply: dict[str, Any] = json.loads(result.stdout)
        return reply

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

    def test_only_navigation_hook_is_registered(self) -> None:
        hooks = json.loads(SCRIPT.with_name("hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(set(hooks), {"PreToolUse"})
        self.assertEqual(hooks["PreToolUse"][0]["matcher"], "Read")

    def test_read_counts_multiple_buffers_and_skips_binary(self) -> None:
        self.write("big.py", "def function():\n    pass\n" + "# line\n" * 30000)
        reply = self.hook("read", tool_input={"file_path": "big.py"})
        self.assertIn("30002 lines", reply["hookSpecificOutput"]["permissionDecisionReason"])
        self.write("binary.dat", "\0\n" * 500)
        self.assertEqual(self.hook("read", tool_input={"file_path": "binary.dat"}), {})

    def test_read_state_is_separate_for_each_session(self) -> None:
        self.write("big.py", "def function():\n    pass\n" + "# line\n" * 400)
        self.assertIn("hookSpecificOutput", self.hook("read", tool_input={"file_path": "big.py"}))
        reply = self.hook("read", session_id="s2", tool_input={"file_path": "big.py"})
        self.assertIn("hookSpecificOutput", reply)

    def test_read_unicode_path_and_final_line_without_newline(self) -> None:
        self.write("длинный файл.py", "def функция():\n    pass\n" + "# line\n" * 399 + "# end")
        reply = self.hook("read", tool_input={"file_path": "длинный файл.py"})
        reason = reply["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("402 lines", reason)
        self.assertIn("функция", reason)

    def test_parallel_reads_preserve_each_file_marker(self) -> None:
        names = [f"big{i}.py" for i in range(4)]
        for name in names:
            self.write(name, "def function():\n    pass\n" + "# line\n" * 400)
        with ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(
                pool.map(lambda name: self.hook("read", tool_input={"file_path": name}), names)
            )
        self.assertTrue(all("hookSpecificOutput" in reply for reply in replies))
        for name in names:
            self.assertEqual(self.hook("read", tool_input={"file_path": name}), {})

    def test_parallel_reads_of_same_file_deny_only_once(self) -> None:
        self.write("big.py", "def function():\n    pass\n" + "# line\n" * 400)
        with ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(
                pool.map(lambda _: self.hook("read", tool_input={"file_path": "big.py"}), range(4))
            )
        self.assertEqual(sum("hookSpecificOutput" in reply for reply in replies), 1)

    def test_read_requires_private_plugin_data(self) -> None:
        self.write("big.py", "def function():\n    pass\n" + "# line\n" * 400)
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in {"CLAUDE_PLUGIN_DATA", "PLUGIN_DATA"}
        }
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "read"],
            input=json.dumps({"cwd": str(self.root), "tool_input": {"file_path": "big.py"}}),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("private plugin data directory", result.stderr)

    def test_vscode_requires_explicit_invocation(self) -> None:
        for name in ("fleex-vscode",):
            skill = SCRIPT.parent.parent / "skills" / name
            self.assertIn(
                "disable-model-invocation: true", (skill / "SKILL.md").read_text(encoding="utf-8")
            )
            self.assertIn(
                "allow_implicit_invocation: false",
                (skill / "agents/openai.yaml").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
