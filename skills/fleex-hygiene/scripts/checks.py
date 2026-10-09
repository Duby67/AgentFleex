"""List the style and static checks a repository configures, with check and fix commands.

Standard library only. Detection reads configuration files, package.json scripts, Makefile targets,
pre-commit, and CI workflow run lines; it never runs a check. `{files}` stands for changed files.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# name, configuration evidence (globs, or "pyproject:<tool>"), check, fix, executable.
TOOLS = [
    ("ruff", ["pyproject:ruff", "ruff.toml", ".ruff.toml"],
     "ruff check {files} && ruff format --check {files}",
     "ruff check --fix {files} && ruff format {files}", "ruff"),
    ("black", ["pyproject:black"], "black --check {files}", "black {files}", "black"),
    ("isort", ["pyproject:isort", ".isort.cfg"], "isort --check-only {files}", "isort {files}",
     "isort"),
    ("flake8", [".flake8", "setup.cfg:flake8", "tox.ini:flake8"], "flake8 {files}", None, "flake8"),
    ("pylint", ["pyproject:pylint", ".pylintrc", "pylintrc"], "pylint {files}", None, "pylint"),
    ("mypy", ["pyproject:mypy", "mypy.ini", ".mypy.ini", "setup.cfg:mypy"], "mypy {files}", None,
     "mypy"),
    ("pyright", ["pyproject:pyright", "pyrightconfig.json"], "pyright {files}", None, "pyright"),
    ("eslint", ["eslint.config.*", ".eslintrc*", "package:eslintConfig"], "npx eslint {files}",
     "npx eslint --fix {files}", "npx"),
    ("prettier", [".prettierrc*", "prettier.config.*", "package:prettier"],
     "npx prettier --check {files}", "npx prettier --write {files}", "npx"),
    ("biome", ["biome.json", "biome.jsonc"], "npx biome check {files}",
     "npx biome check --write {files}", "npx"),
    ("tsc", ["tsconfig.json"], "npx tsc --noEmit", None, "npx"),
    ("gofmt", ["go.mod"], "gofmt -l {files}", "gofmt -w {files}", "gofmt"),
    ("go vet", ["go.mod"], "go vet ./...", None, "go"),
    ("golangci-lint", [".golangci.yml", ".golangci.yaml", ".golangci.toml"], "golangci-lint run",
     "golangci-lint run --fix", "golangci-lint"),
    ("rustfmt", ["Cargo.toml"], "cargo fmt --check", "cargo fmt", "cargo"),
    ("clippy", ["Cargo.toml"], "cargo clippy -- -D warnings", None, "cargo"),
    ("shellcheck", [".shellcheckrc"], "shellcheck {files}", None, "shellcheck"),
    ("markdownlint", [".markdownlint*"], "npx markdownlint-cli2 {files}",
     "npx markdownlint-cli2 --fix {files}", "npx"),
    ("yamllint", [".yamllint", ".yamllint.y*ml"], "yamllint {files}", None, "yamllint"),
    ("pre-commit", [".pre-commit-config.yaml"], "pre-commit run --files {files}", None,
     "pre-commit"),
]
PYTHON_TOOLS = {"ruff", "black", "isort", "flake8", "pylint", "mypy", "pyright"}
SCRIPT = re.compile(r"^(lint|format|fmt|typecheck|type-check|check|style)([:-]\w+)*$")
TARGET = re.compile(r"^((?:lint|format|fmt|typecheck|check|style)[\w-]*):(?!=)", re.M)
CI_RUN = re.compile(r"^\s*(?:-\s*)?run:\s*\|?\s*(.*)$")
CI_TOOLS = re.compile(r"\b(" + "|".join(re.escape(t[0].split()[0]) for t in TOOLS) +
                      r"|lint|fmt|format|typecheck)\b")


def configured(root: Path, evidence: list[str], package: dict) -> str:
    """The first file or section proving the tool is configured, or an empty string."""
    for item in evidence:
        source, _, section = item.partition(":")
        if source == "pyproject":
            text = read(root / "pyproject.toml")
            if re.search(rf"^\[tool\.{section}\b", text, re.M):
                return f"pyproject.toml [tool.{section}]"
        elif source == "package":
            if section in package or section in package.get("devDependencies", {}):
                return f"package.json {section}"
        elif section:
            if re.search(rf"^\[(tool:)?{section}\]", read(root / source), re.M):
                return f"{source} [{section}]"
        else:
            found = sorted(root.glob(source))
            if found:
                return found[0].name
    return ""


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def python_env(root: Path) -> tuple[str, str]:
    """Command prefix that runs tools from the project environment, and the executable it needs."""
    for lock, tool in (("uv.lock", "uv"), ("poetry.lock", "poetry"), ("pdm.lock", "pdm")):
        if (root / lock).exists():
            return f"{tool} run ", tool
    for bin_dir in (".venv/bin", ".venv/Scripts"):
        if (root / bin_dir).is_dir():
            return f"{bin_dir}/", ""
    return "", ""


def runner(root: Path) -> str:
    for lock, tool in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun")):
        if (root / lock).exists():
            return tool
    return "npm"


def rows(root: Path) -> list[str]:
    try:
        package = json.loads(read(root / "package.json") or "{}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"checks: package.json is not valid JSON: {error}")
    result = []
    prefix, env_tool = python_env(root)
    for name, evidence, check, fix, executable in TOOLS:
        source = configured(root, evidence, package)
        if not source:
            continue
        found = shutil.which(executable)
        if name in PYTHON_TOOLS and prefix:
            check = check.replace(f"{name} ", f"{prefix}{name} ")
            fix = fix and fix.replace(f"{name} ", f"{prefix}{name} ")
            # A lock file means the environment manager runs the tool; a bare .venv must hold it.
            executable = env_tool or f"{prefix}{name}"
            found = shutil.which(env_tool) if env_tool else any(
                (root / prefix / f"{name}{suffix}").exists() for suffix in ("", ".exe"))
        missing = "" if found else f"  MISSING {executable}"
        result.append(f"{name} ({source}){missing}\n  check: {check}"
                      + (f"\n  fix: {fix}" if fix else ""))
    npm = runner(root)
    for script in sorted(package.get("scripts", {})):
        if SCRIPT.match(script):
            missing = "" if shutil.which(npm) else f"  MISSING {npm}"
            result.append(f"package.json script {script}{missing}\n  run: {npm} run {script}")
    for target in TARGET.findall(read(root / "Makefile")):
        missing = "" if shutil.which("make") else "  MISSING make"
        result.append(f"Makefile target {target}{missing}\n  run: make {target}")
    for workflow in sorted((root / ".github" / "workflows").glob("*.y*ml")):
        for line in read(workflow).splitlines():
            match = CI_RUN.match(line)
            if match and CI_TOOLS.search(match.group(1)):
                result.append(f"CI {workflow.name}\n  run: {match.group(1).strip()[:160]}")
    if (root / ".editorconfig").exists():
        result.append(".editorconfig\n  follow it in every edited file")
    result.append("git whitespace\n  check: git diff --check HEAD")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="directory inside the repository")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=args.root,
                         capture_output=True, text=True)
    if top.returncode:
        where = Path(args.root).resolve()
        print(f"checks: {where} is not inside a git repository", file=sys.stderr)
        return 1
    print("\n".join(rows(Path(top.stdout.strip()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
