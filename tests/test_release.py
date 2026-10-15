"""Behavior of .github/scripts/release.py on small repositories."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".github/scripts/release.py"
LINK = "https://github.com/o/r/releases/tag"


class ReleaseTest(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        for args in (["user.name", "t"], ["user.email", "t@t"], ["commit.gpgsign", "false"]):
            subprocess.run(["git", "config", *args], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "--allow-empty", "-m", "x"], cwd=self.root, check=True
        )
        subprocess.run(["git", "tag", "1.0.0"], cwd=self.root, check=True)
        self.write("1.1.0", "", "- New.\n", "- Новое.\n")

    def write(self, version: str, unreleased: str, notes: str, ru: str) -> None:
        (self.root / "pyproject.toml").write_text(
            f'[project]\nversion = "{version}"\n', encoding="utf-8"
        )
        for manifest in (".claude-plugin", ".codex-plugin"):
            (self.root / manifest).mkdir(exist_ok=True)
            (self.root / manifest / "plugin.json").write_text(
                json.dumps({"version": version}), encoding="utf-8"
            )
        head = "## Unreleased\n\n" + unreleased + "\n"
        body = f"## [{version}]({LINK}/{version})\n\n{{}}\n## [1.0.0]({LINK}/1.0.0)\n\n- Old.\n"
        (self.root / "docs/ru").mkdir(parents=True, exist_ok=True)
        (self.root / "docs/CHANGELOG.md").write_text(
            "# Changelog\n\n**English** · [Русский](ru/CHANGELOG.md)\n\n"
            + head
            + body.format(notes),
            encoding="utf-8",
        )
        (self.root / "docs/ru/CHANGELOG.md").write_text(
            "# Changelog\n\n[English](../CHANGELOG.md) · **Русский**\n\n" + head + body.format(ru),
            encoding="utf-8",
        )

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def test_new_version_is_releasable(self) -> None:
        run = self.run_script("check", "--release")
        self.assertEqual((run.returncode, run.stdout), (0, "1.1.0\n"), run.stderr)

    def test_notes_collapse_translations(self) -> None:
        run = self.run_script("notes")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(run.stdout.startswith("- New.\n"))
        self.assertIn("<details><summary>Русский</summary>\n\n- Новое.\n", run.stdout)

    def test_notes_use_utf8_with_cp1252_stdout(self) -> None:
        run = subprocess.run(
            [sys.executable, str(SCRIPT), "notes"],
            cwd=self.root,
            env={**os.environ, "PYTHONIOENCODING": "cp1252"},
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("<summary>Русский</summary>\n\n- Новое.\n", run.stdout)

    def test_unreleased_items_pass_check_but_block_release(self) -> None:
        self.write("1.1.0", "- Pending.\n", "- New.\n", "- Новое.\n")
        self.assertEqual(self.run_script("check").returncode, 0)
        run = self.run_script("check", "--release")
        self.assertEqual(run.returncode, 1)
        self.assertIn("move the ## Unreleased items", run.stderr)

    def test_tagged_version_blocks_release(self) -> None:
        subprocess.run(["git", "tag", "1.1.0"], cwd=self.root, check=True)
        run = self.run_script("check", "--release")
        self.assertIn("tag 1.1.0 already exists", run.stderr)

    def test_version_below_latest_tag_blocks_release(self) -> None:
        subprocess.run(["git", "tag", "1.10.0"], cwd=self.root, check=True)
        run = self.run_script("check", "--release")
        self.assertIn("not above the latest tag 1.10.0", run.stderr)

    def test_differing_manifests_fail(self) -> None:
        (self.root / ".codex-plugin/plugin.json").write_text(
            json.dumps({"version": "1.2.0"}), encoding="utf-8"
        )
        run = self.run_script("check")
        self.assertIn("version differs from pyproject.toml", run.stderr)

    def test_sync_updates_both_manifests_and_preserves_other_fields(self) -> None:
        self.write("1.2.0", "", "- New.\n", "- Новое.\n")
        for manifest in (".claude-plugin", ".codex-plugin"):
            (self.root / manifest / "plugin.json").write_text(
                json.dumps({"version": "1.1.0", "name": "test"}), encoding="utf-8"
            )
        self.assertNotEqual(self.run_script("check").returncode, 0)
        run = self.run_script("sync")
        self.assertEqual(run.returncode, 0, run.stderr)
        for manifest in (".claude-plugin", ".codex-plugin"):
            found = json.loads((self.root / manifest / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(found, {"version": "1.2.0", "name": "test"})
        self.assertEqual(self.run_script("check").returncode, 0)

    def test_invalid_project_version_does_not_change_manifests(self) -> None:
        path = self.root / ".claude-plugin/plugin.json"
        before = path.read_bytes()
        (self.root / "pyproject.toml").write_text(
            '[project]\nversion = "invalid"\n', encoding="utf-8"
        )
        run = self.run_script("sync")
        self.assertEqual(run.returncode, 1)
        self.assertIn("project.version", run.stderr)
        self.assertEqual(path.read_bytes(), before)

    def test_translation_headings_must_match(self) -> None:
        path = self.root / "docs/ru/CHANGELOG.md"
        text = path.read_text(encoding="utf-8").replace("## [1.0.0]", "## [0.9.0]")
        path.write_text(text, encoding="utf-8")
        run = self.run_script("check")
        self.assertIn("docs/ru/CHANGELOG.md: headings must match", run.stderr)

    def test_empty_translation_notes_block_release(self) -> None:
        self.write("1.1.0", "", "- New.\n", "")
        run = self.run_script("check", "--release")
        self.assertIn("docs/ru/CHANGELOG.md: no notes under ## [1.1.0]", run.stderr)


if __name__ == "__main__":
    unittest.main()
