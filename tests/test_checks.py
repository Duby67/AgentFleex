"""Behavior of skills/fleex-hygiene/scripts/checks.py on small repositories."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills/fleex-hygiene/scripts/checks.py"


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
        self.assertIn("assets/ruff.toml", output)

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
