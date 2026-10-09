"""List the style and static checks a repository configures, with check and fix commands.

Standard library only. Detection reads configuration files, package.json scripts, Makefile targets,
pre-commit, and CI commands; it never runs a check. `{files}` stands for changed files. A tool that
cannot run is marked MISSING (install it) or SETUP (install the project environment).
"""

from __future__ import annotations

import argparse
import io
import json
import os
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
TARGET = re.compile(r"^((?:lint|format|fmt|typecheck|check|style)[\w-]*):(?!=)", re.MULTILINE)
CI_FILES = [".github/workflows/*.y*ml", ".gitlab-ci.yml", ".circleci/config.yml",
            "azure-pipelines.yml", "bitbucket-pipelines.yml", ".travis.yml", ".drone.yml",
            ".woodpecker.y*ml", ".woodpecker/*.y*ml", ".buildkite/pipeline.y*ml"]
# YAML keys whose value, block scalar, or list items are shell commands.
CI_KEY = re.compile(r"^(\s*)(?:-\s+)?(?:run|script|before_script|after_script|command|commands|"
                    r"bash|sh|pwsh|powershell)\s*:\s*(.*)$")
JENKINS_SH = re.compile(r"\b(?:sh|bat|powershell)\s*\(?\s*(?:script:\s*)?['\"]{1,3}(.+?)['\"]{1,3}")
# Configured tool names, or a lint-like task run through a task runner or package manager.
CI_TOOLS = re.compile(r"\b(" + "|".join(re.escape(t[0]) for t in TOOLS) + r"|cargo (fmt|clippy))\b|"
                      r"\b(make|just|task|npm|pnpm|yarn|bun)\s+(run\s+)?"
                      r"(lint|format|fmt|typecheck|type-check|check|style)\b")
INSTALL = re.compile(r"^\S+(\s+(tool|global|-g))?\s+(install|i|add|sync)\b")
YAML_MAPPING = re.compile(r"^\s*[\w-]+:(\s|$)")


def configured(root: Path, evidence: list[str], package: dict) -> str:
    """The first file or section proving the tool is configured, or an empty string."""
    for item in evidence:
        source, _, section = item.partition(":")
        if source == "pyproject":
            text = read(root / "pyproject.toml")
            if re.search(rf"^\[tool\.{section}\b", text, re.MULTILINE):
                return f"pyproject.toml [tool.{section}]"
        elif source == "package":
            if section in package or section in package.get("devDependencies", {}):
                return f"package.json {section}"
        elif section:
            if re.search(rf"^\[(tool:)?{section}\]", read(root / source), re.MULTILINE):
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


def python_env(root: Path) -> tuple[str, str, Path | None]:
    """Command prefix, environment manager, and environment directory of a Python project."""
    for lock, tool in (("uv.lock", "uv"), ("poetry.lock", "poetry"), ("pdm.lock", "pdm")):
        if not (root / lock).exists():
            continue
        if tool == "poetry":
            env = None
            if shutil.which("poetry"):
                info = subprocess.run(["poetry", "env", "info", "--path"], cwd=root,
                                      capture_output=True, text=True, check=False)
                env = Path(info.stdout.strip()) if not info.returncode else None
        else:
            env = root / os.environ.get("UV_PROJECT_ENVIRONMENT", ".venv")
        return f"{tool} run ", tool, env
    venv = root / ".venv"
    return ("", "", venv) if venv.is_dir() else ("", "", None)


def in_env(env: Path | None, name: str) -> bool:
    return env is not None and any((env / folder / f"{name}{suffix}").exists()
                                   for folder in ("bin", "Scripts") for suffix in ("", ".exe"))


def runner(root: Path) -> str:
    for lock, tool in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"), ("bun.lockb", "bun")):
        if (root / lock).exists():
            return tool
    return "npm"


def node_status(root: Path, npm: str, binary: str) -> str:
    """Why a Node tool cannot run from the project, or an empty string."""
    if not shutil.which(npm):
        return f"  MISSING {npm}"
    if not (root / "node_modules").is_dir():
        return f"  SETUP: {npm} install"
    if binary and not any((root / "node_modules" / ".bin" / f"{binary}{suffix}").exists()
                          for suffix in ("", ".cmd")):
        return f"  MISSING {binary} in node_modules; npx would download it"
    return ""


def ci_commands(path: Path) -> list[tuple[int, str]]:
    """Shell commands with line numbers from a CI file: values, block scalars, and list items."""
    lines = read(path).splitlines()
    if path.name == "Jenkinsfile":
        return [(n, m.group(1)) for n, line in enumerate(lines, 1)
                for m in JENKINS_SH.finditer(line)]
    commands, number = [], 0
    while number < len(lines):
        match = CI_KEY.match(lines[number])
        number += 1
        if not match:
            continue
        level, value = len(match.group(1)), match.group(2).strip()
        if value and value[0] not in "|>":
            commands.append((number, value.strip("'\"")))
            continue
        following = next((line for line in lines[number:] if line.strip()), "")
        if not value and YAML_MAPPING.match(following):
            continue  # A nested mapping such as CircleCI's run: {name, command}; scan it as keys.
        # Block scalar or list: every deeper line until the indentation returns to the key's level.
        pending = ""
        while number < len(lines):
            line = lines[number]
            if line.strip() and len(line) - len(line.lstrip()) <= level:
                break
            number += 1
            command = re.sub(r"^-\s+", "", line.strip()).strip("'\"")
            if not command or command[0] in "|>#":
                continue
            # Join shell line continuations into one command.
            pending = f"{pending} {command}".strip()
            if not pending.endswith("\\"):
                commands.append((number, pending))
                pending = ""
            else:
                pending = pending[:-1].rstrip()
    return commands


def rows(root: Path) -> list[str]:
    try:
        package = json.loads(read(root / "package.json") or "{}")
    except json.JSONDecodeError as error:
        raise SystemExit(f"checks: package.json is not valid JSON: {error}") from None
    result = []
    prefix, manager, env = python_env(root)
    npm = runner(root)
    for name, evidence, check, fix, executable in TOOLS:
        source = configured(root, evidence, package)
        if not source:
            continue
        status = "" if shutil.which(executable) else f"  MISSING {executable}"
        if name in PYTHON_TOOLS and (manager or env):
            if manager:
                check = check.replace(f"{name} ", f"{prefix}{name} ")
                fix = fix and fix.replace(f"{name} ", f"{prefix}{name} ")
            else:
                check = check.replace(f"{name} ", f".venv/bin/{name} ")
                fix = fix and fix.replace(f"{name} ", f".venv/bin/{name} ")
            install = {"uv": "uv sync", "poetry": "poetry install", "pdm": "pdm install"}
            if manager and not shutil.which(manager):
                status = f"  MISSING {manager}"
            elif not in_env(env, name):
                status = (f"  SETUP: {install[manager]} ({name} is not in the project environment)"
                          if manager else f"  MISSING {name} in .venv")
            else:
                status = ""
        elif executable == "npx":
            status = node_status(root, npm, check.split()[1])
        result.append(f"{name} ({source}){status}\n  check: {check}"
                      + (f"\n  fix: {fix}" if fix else ""))
    for script in sorted(package.get("scripts", {})):
        if SCRIPT.match(script):
            status = node_status(root, npm, "")
            result.append(f"package.json script {script}{status}\n  run: {npm} run {script}")
    for target in TARGET.findall(read(root / "Makefile")):
        status = "" if shutil.which("make") else "  MISSING make"
        result.append(f"Makefile target {target}{status}\n  run: make {target}")
    ci_files = sorted({p for pattern in CI_FILES for p in root.glob(pattern)} |
                      ({root / "Jenkinsfile"} if (root / "Jenkinsfile").exists() else set()))
    for path in ci_files:
        for number, command in ci_commands(path):
            if CI_TOOLS.search(command) and not INSTALL.match(command):
                where = path.relative_to(root).as_posix()
                result.append(f"CI {where}:{number}\n  run: {command[:160]}")
    if (root / ".vscode" / "settings.json").exists():
        result.append(".vscode/settings.json\n  its linter settings are part of the style")
    if (root / ".editorconfig").exists():
        result.append(".editorconfig\n  follow it in every edited file")
    result.append("git whitespace\n  check: git diff --check HEAD")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="directory inside the repository")
    args = parser.parse_args()
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=args.root,
                         capture_output=True, text=True, check=False)
    if top.returncode:
        where = Path(args.root).resolve()
        print(f"checks: {where} is not inside a git repository", file=sys.stderr)
        return 1
    print("\n".join(rows(Path(top.stdout.strip()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
