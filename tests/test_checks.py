"""Behavior of skills/fleex-hygiene/scripts/checks.py on small repositories."""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "skills/fleex-hygiene/scripts/checks.py"
SPEC = importlib.util.spec_from_file_location("checks", SCRIPT)
assert SPEC and SPEC.loader
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class ChecksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, text: str = "") -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # Bytes keep LF line endings on Windows too.
        path.write_bytes(textwrap.dedent(text).encode("utf-8"))

    def checks(self, path: str = os.environ.get("PATH", "")) -> str:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "PATH": path},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_configured_tool_wins_over_default(self) -> None:
        self.write("pyproject.toml", "[tool.black]\n[tool.pyright]\n")
        self.write("app.py")
        output = self.checks()
        self.assertIn("black (pyproject.toml [tool.black])", output)
        self.assertIn("pyright (pyproject.toml [tool.pyright])", output)
        self.assertNotIn("AgentFleex default", output)

    def test_defaults_fill_unconfigured_roles(self) -> None:
        self.write("app.py")
        self.write("run.sh")
        output = self.checks()
        self.assertIn("ruff (AgentFleex default", output)
        self.assertIn("mypy (AgentFleex default", output)
        self.assertIn("shellcheck (built-in rules)", output)
        self.assertNotIn("markdownlint (", output)
        self.write("README.md", "# Title\n")
        self.write("ci.yml", "on: push\n")
        output = self.checks()
        self.assertIn("markdownlint (AgentFleex default", output)
        self.assertIn("yamllint (AgentFleex default", output)
        self.assertIn("assets/ruff.toml", output)
        self.assertNotIn("\\", output)
        self.assertNotIn("'", output)

    def test_pre_commit_runs_the_tools_it_lists(self) -> None:
        self.write("ruff.toml")
        self.write("app.py")
        self.write(".pre-commit-config.yaml", "repos:\n  - hooks:\n      - id: ruff-check\n")
        output = self.checks()
        self.assertIn("pre-commit (.pre-commit-config.yaml)", output)
        self.assertNotIn("ruff (", output)
        self.assertIn("mypy (AgentFleex default", output)

    def test_no_python_means_no_python_defaults(self) -> None:
        self.write("README.md", "# Title\n")
        self.assertNotIn("ruff", self.checks())

    def test_environment_states(self) -> None:
        self.write("pyproject.toml", "[tool.ruff]\n[tool.mypy]\n")
        self.write(".venv/bin/ruff")
        output = self.checks()
        self.assertIn("ruff (pyproject.toml [tool.ruff])\n  check: .venv/bin/ruff", output)
        self.assertIn("mypy (pyproject.toml [tool.mypy])  MISSING mypy in .venv", output)
        self.write("uv.lock")
        output = self.checks()
        if "MISSING uv" not in output:
            self.assertIn("SETUP: uv sync (mypy is not in the project environment)", output)
            self.assertIn("check: uv run ruff check", output)

    @unittest.skipIf(os.name == "nt", "the fake poetry is a POSIX shell script")
    def test_poetry_is_never_executed(self) -> None:
        marker = self.root / "poetry-ran"
        self.write("bin/poetry", f"#!/bin/sh\ntouch '{marker}'\n")
        (self.root / "bin/poetry").chmod(0o755)
        self.write("pyproject.toml", "[tool.ruff]\n")
        self.write("poetry.lock")
        path = f"{self.root / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"
        output = self.checks(path)
        self.assertFalse(marker.exists())
        self.assertIn("check: poetry run ruff check", output)
        self.assertNotIn("SETUP", output)
        self.write(".venv/bin/mypy")
        self.write("pyproject.toml", "[tool.ruff]\n[tool.mypy]\n")
        output = self.checks(path)
        self.assertIn("SETUP: poetry install (ruff is not in the project environment)", output)
        self.assertNotIn("SETUP: poetry install (mypy", output)
        self.assertFalse(marker.exists())

    def test_percent_in_a_generated_path_fails(self) -> None:
        with self.assertRaises(SystemExit) as raised:
            checks.shell_path(Path("C:/Users/a%USERNAME%b/ruff.toml"))
        self.assertIn("contains '%'", str(raised.exception))
        self.assertEqual(checks.shell_path(Path("/opt/a b/ruff.toml")), '"/opt/a b/ruff.toml"')

    def test_uvx_defaults_are_pinned_to_the_pre_commit_versions(self) -> None:
        with mock.patch.object(checks.shutil, "which", lambda name: name == "uvx"):
            self.assertEqual(checks.default_tool("ruff")[0], "uvx ruff@0.16.9")
            self.assertEqual(checks.default_tool("mypy")[0], "uvx mypy@2.3.1")
        with mock.patch.object(checks.shutil, "which", lambda name: name == "npx"):
            self.assertEqual(
                checks.npx_tool("markdownlint-cli2"), ("npx --yes markdownlint-cli2@0.23.3", "")
            )
        hooks = (SCRIPT.parents[3] / ".pre-commit-config.yaml").read_text(encoding="utf-8")
        pinned = {**checks.UVX_VERSIONS, **checks.NPX_VERSIONS}
        for name, repo in (
            ("ruff", "ruff-pre-commit"),
            ("mypy", "mirrors-mypy"),
            ("yamllint", "yamllint"),
            ("markdownlint-cli2", "markdownlint-cli2"),
        ):
            frozen = re.search(rf"{repo}\n\s+rev: \S+ # frozen: v(\S+)", hooks)
            self.assertIsNotNone(frozen, repo)
            assert frozen
            self.assertEqual(pinned[name], frozen.group(1), name)

    def test_windows_venv_layout(self) -> None:
        self.write("pyproject.toml", "[tool.ruff]\n")
        self.write(".venv/Scripts/ruff.exe")
        output = self.checks()
        self.assertIn("ruff (pyproject.toml [tool.ruff])\n  check: .venv/Scripts/ruff", output)
        self.assertNotIn(".venv/bin/", output)

    def test_node_without_modules_needs_setup(self) -> None:
        self.write("package.json", '{"scripts": {"lint": "eslint ."}}')
        self.write("eslint.config.js")
        output = self.checks()
        if "MISSING npm" not in output:
            self.assertIn("eslint (eslint.config.js)  SETUP: npm install", output)
            self.assertIn("package.json script lint  SETUP: npm install", output)

    def test_makefile_targets_keep_full_names(self) -> None:
        self.write("Makefile", "lint:\n\ttrue\ncheck-all: lint\nFOO:=1\nbuild:\n\ttrue\n")
        output = self.checks()
        self.assertIn("run: make lint", output)
        self.assertIn("run: make check-all", output)
        self.assertNotIn("make build", output)

    def test_ci_formats(self) -> None:
        self.write(
            ".github/workflows/ci.yml",
            """\
            jobs:
              x:
                steps:
                  - run: |
                      pnpm install
                      pnpm lint
                      uv export --format requirements-txt \\
                        --no-dev
                  - run: go test ./...
                  - run: go vet ./...
                  - run: >-
                      uvx mypy --strict
                      src
            """,
        )
        self.write(
            ".gitlab-ci.yml",
            """\
            lint:
              before_script:
                - pip install ruff
              script:
                - ruff check .
                - |
                  mypy src
            """,
        )
        self.write(
            ".circleci/config.yml",
            """\
            jobs:
              b:
                steps:
                  - run:
                      name: fmt
                      command: cargo fmt --check
            """,
        )
        self.write("Jenkinsfile", "steps { sh 'make lint'; sh \"eslint .\" }\n")
        commands = [
            line.removeprefix("  run: ") for line in self.checks().splitlines() if "  run: " in line
        ]
        self.assertEqual(
            sorted(commands),
            sorted(
                [
                    "pnpm lint",
                    "go vet ./...",
                    "uvx mypy --strict src",
                    "ruff check .",
                    "mypy src",
                    "cargo fmt --check",
                    "make lint",
                    "eslint .",
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
