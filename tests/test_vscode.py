"""Behavior of skills/fleex-vscode/scripts/vscode.py against a fake VS Code CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills/fleex-vscode/scripts/vscode.py"
PACKS = ROOT / "skills/fleex-vscode/assets/packs"

# Logs its arguments; opening a window with a new profile registers it, as VS Code does.
FAKE = """\
import json, sys
from pathlib import Path
user, log = Path(sys.argv[1]), Path(sys.argv[2])
args = sys.argv[3:]
with log.open("a") as out:
    out.write(json.dumps(args) + "\\n")
if "--new-window" in args:
    storage = user / "globalStorage/storage.json"
    storage.parent.mkdir(parents=True, exist_ok=True)
    name = args[args.index("--profile") + 1]
    data = {"userDataProfiles": [{"location": "abc123", "name": name}]}
    storage.write_text(json.dumps(data))
"""


class VSCodeTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.user = self.dir / "User"
        self.user.mkdir()
        self.log = self.dir / "log.jsonl"
        self.vsix = self.dir / "vsix"
        self.vsix.mkdir()
        for pack in PACKS.iterdir():
            (self.vsix / f"fleex-pack-{pack.name}-1.0.0.vsix").write_text("")
        (self.dir / "fake.py").write_text(FAKE)
        argv = f'"{sys.executable}" "{self.dir / "fake.py"}" "{self.user}" "{self.log}"'
        if os.name == "nt":
            self.code = self.dir / "code.cmd"
            self.code.write_text(f"@{argv} %*\n")
        else:
            self.code = self.dir / "code"
            self.code.write_text(f'#!/bin/sh\nexec {argv} "$@"\n')
            self.code.chmod(0o755)

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(SCRIPT), *args]
        if args[:1] == ("apply",):
            command += ["--code", str(self.code), "--user-dir", str(self.user)]
            command += ["--vsix", str(self.vsix)]
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def calls(self) -> list[list[str]]:
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def test_list_names_every_pack_and_profile(self) -> None:
        run = self.run_script("list")
        self.assertEqual(run.returncode, 0, run.stderr)
        for pack in PACKS.iterdir():
            self.assertIn(f"pack {pack.name}:", run.stdout)
        self.assertIn("profile Python: minimal, python", run.stdout)

    def test_new_profile_is_created_then_gets_packs_and_settings(self) -> None:
        settings = self.user / "profiles/abc123/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text('{"kept": 1}')
        run = self.run_script("apply", "Python", "--add", "infrastructure")
        self.assertEqual(run.returncode, 0, run.stderr)
        calls = self.calls()
        self.assertEqual(calls[0], ["--profile", "Python", "--new-window"])
        installed = [Path(call[1]).name for call in calls[1:]]
        self.assertEqual(
            installed,
            [f"fleex-pack-{name}-1.0.0.vsix" for name in ("minimal", "python", "infrastructure")],
        )
        self.assertTrue(all(call[-2:] == ["--profile", "Python"] for call in calls[1:]))
        self.assertEqual(json.loads(settings.read_text())["kept"], 1)

    def test_default_profile_uses_user_settings_without_profile_flag(self) -> None:
        run = self.run_script("apply", "Default")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(all("--profile" not in call for call in self.calls()))
        self.assertTrue((self.user / "settings.json").is_file())

    def test_settings_with_comments_fail_without_writing(self) -> None:
        settings = self.user / "settings.json"
        settings.write_text('{\n  // mine\n  "a": 1,\n}\n')
        run = self.run_script("apply", "Default")
        self.assertEqual(run.returncode, 1)
        self.assertIn("not plain JSON", run.stderr)
        self.assertIn("// mine", settings.read_text())
        self.assertFalse(self.log.exists())

    def test_unknown_pack_fails_before_any_call(self) -> None:
        run = self.run_script("apply", "Python", "--add", "nope")
        self.assertEqual(run.returncode, 1)
        self.assertIn("unknown packs nope", run.stderr)
        self.assertFalse(self.log.exists())

    def test_missing_vsix_fails(self) -> None:
        (self.vsix / "fleex-pack-python-1.0.0.vsix").unlink()
        run = self.run_script("apply", "Python")
        self.assertEqual(run.returncode, 1)
        self.assertIn("fleex-pack-python-*.vsix, found 0", run.stderr)


if __name__ == "__main__":
    unittest.main()
