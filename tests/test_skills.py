"""Always-loaded context budget, and check.sh and check.ps1 on small repositories."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills/fleex-skills/scripts"
# Characters loaded into every request; raise a limit only on purpose, so growth is a decision.
AGENTS_BUDGET = 3300
DESCRIPTIONS_BUDGET = 2100

# A repository with one error of each kind the scripts report.
BROKEN = {
    "CLAUDE.md": "@AGENTS.md\n",
    "AGENTS.md": "# Project\n\nUse $fleex-nope for nothing.\n",
    "README.md": "# Readme\n\nSee [the guide](docs/missing.md).\n",
    "skills/good/SKILL.md": "---\nname: good\ndescription: Does one thing well.\n---\n\n# Good\n",
    "skills/wrong/SKILL.md": "---\nname: other\ndescription: Name differs.\n---\n\n# Wrong\n",
    "skills/gated/SKILL.md": (
        "---\nname: gated\ndescription: User-gated without Codex policy.\n"
        "disable-model-invocation: true\n---\n\n# Gated\n"
    ),
}


def description(skill: Path) -> str:
    for line in skill.read_text(encoding="utf-8").splitlines()[1:]:
        if line == "---":
            break
        if line.startswith("description: "):
            return line.removeprefix("description: ")
    return ""


class BudgetTest(unittest.TestCase):
    def test_always_loaded_context_stays_within_budget(self) -> None:
        agents = len((ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertLessEqual(agents, AGENTS_BUDGET, "AGENTS.md grew past its budget")
        loaded = [
            skill
            for skill in sorted((ROOT / "skills").glob("*/SKILL.md"))
            if "\ndisable-model-invocation: true\n" not in skill.read_text(encoding="utf-8")
        ]
        total = sum(len(description(skill)) for skill in loaded)
        self.assertLessEqual(
            total, DESCRIPTIONS_BUDGET, "skill descriptions grew past their budget"
        )


# Windows runs check.ps1 alone: its bash may be WSL, outside the checkout.
@unittest.skipIf(os.name == "nt", "check.sh runs on POSIX systems")
class CheckScriptsTest(unittest.TestCase):
    def repository(self, files: dict[str, str]) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(textwrap.dedent(text).encode("utf-8"))
        return root

    def run_check(self, shell: str, root: Path) -> tuple[int, str, list[str]]:
        if shell == "bash":
            command = ["bash", str(SCRIPTS / "check.sh")]
        else:
            command = ["pwsh", "-NoProfile", "-File", str(SCRIPTS / "check.ps1")]
        run = subprocess.run(
            command, cwd=root, capture_output=True, text=True, encoding="utf-8", check=False
        )
        return run.returncode, run.stdout.strip(), sorted(run.stderr.splitlines())

    @unittest.skipUnless(shutil.which("bash"), "needs bash")
    def test_check_sh_reports_each_error(self) -> None:
        code, _, errors = self.run_check("bash", self.repository(BROKEN))
        self.assertEqual(code, 1)
        expected = [
            "AGENTS.md: unknown skill reference $fleex-nope",
            "CLAUDE.md: move to .claude/CLAUDE.md containing exactly '@../AGENTS.md'",
            "README.md: broken link docs/missing.md",
            "skills/gated/SKILL.md: user-gated skill needs agents/openai.yaml with "
            "policy.allow_implicit_invocation: false",
            "skills/wrong/SKILL.md: name 'other' must match directory 'wrong'",
        ]
        self.assertEqual(errors, expected)
        clean = {name: text for name, text in BROKEN.items() if name.startswith("skills/good/")}
        self.assertEqual(self.run_check("bash", self.repository(clean)), (0, "check: ok", []))

    @unittest.skipUnless(shutil.which("bash") and shutil.which("pwsh"), "needs bash and pwsh")
    def test_check_ps1_matches_check_sh(self) -> None:
        clean = {name: text for name, text in BROKEN.items() if name.startswith("skills/good/")}
        for files in (BROKEN, clean):
            root = self.repository(files)
            self.assertEqual(self.run_check("pwsh", root), self.run_check("bash", root))


if __name__ == "__main__":
    unittest.main()
