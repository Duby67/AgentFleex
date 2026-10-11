"""AgentFleex hooks for Claude Code and Codex: style checks on stop, outlines before reading.

Standard library only. Reads the hook event as JSON on stdin and prints the reply as JSON on stdout.

- `stop`: runs the fleex-hygiene checks that take files on the files changed against HEAD, once per
  distinct state of those files, and blocks the stop with the failures. A stop that a stop hook
  already continued is let through, so a failure the agent cannot fix never loops. Linters run the
  repository's own configuration, which can execute code, so they run only after the user agreed
  for that repository and that set of tools; until then the stop asks the agent to ask once.
- `consent yes|no <root>`: records the user's answer for the repository's current set of tools.
- `read`: denies the first whole-file Read of a long file in a session and returns its fleex-index
  outline, so the agent reads only the ranges it needs; repeating the Read reads the whole file.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN / "skills" / "fleex-hygiene" / "scripts"))
import checks  # noqa: E402

INDEX = PLUGIN / "skills" / "fleex-index" / "scripts" / "index.py"
# Lines above which a whole-file Read gets an outline instead.
LONG = 400
PYTHON = (".py", ".pyi")
SCRIPTS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue")
# File types each tool checks; tools not listed here are left to the agent.
FILES = {
    **dict.fromkeys(("ruff", "black", "isort", "flake8", "pylint", "mypy", "pyright"), PYTHON),
    "eslint": SCRIPTS,
    "prettier": SCRIPTS + (".css", ".scss", ".less", ".json", ".md", ".yaml", ".yml", ".html"),
    "biome": SCRIPTS + (".json", ".jsonc", ".css"),
    "gofmt": (".go",),
    "shellcheck": (".sh", ".bash"),
    "markdownlint": (".md",),
    "yamllint": (".yml", ".yaml"),
}
TIMEOUT = 120
OUTPUT = 4000


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def top(cwd: str) -> Path | None:
    result = git(Path(cwd), "rev-parse", "--show-toplevel")
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def data() -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("PLUGIN_DATA")
    return Path(base) if base else Path(tempfile.gettempdir()) / "agentfleex"


def state_path(event: dict[str, Any]) -> Path:
    session = re.sub(r"[^\w-]", "_", str(event.get("session_id") or "default"))
    return data() / "sessions" / f"{session}.json"


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def changed(root: Path) -> list[str]:
    """Existing files that differ from HEAD, plus untracked ones that are not ignored."""
    if git(root, "rev-parse", "--verify", "-q", "HEAD").returncode == 0:
        names = git(root, "diff", "--name-only", "HEAD").stdout.splitlines()
    else:
        names = git(root, "ls-files", "--cached").stdout.splitlines()
    names += git(root, "ls-files", "--others", "--exclude-standard").stdout.splitlines()
    return sorted({n for n in names if (root / n).is_file()})


def fingerprint(root: Path, files: list[str]) -> str:
    digest = hashlib.sha1()
    for name in files:
        stat = (root / name).stat()
        digest.update(f"{name}\0{stat.st_size}\0{stat.st_mtime_ns}\0".encode())
    return digest.hexdigest()


def quote(names: list[str]) -> str:
    if os.name == "nt":
        return " ".join(f'"{n}"' if re.search(r"[^\w@%+=:,./-]", n) else n for n in names)
    return " ".join(shlex.quote(n) for n in names)


def entries(root: Path) -> list[tuple[str, str, str, str]]:
    """Name, title, check, and fix command of every check checks.py lists."""
    result = []
    for row in checks.rows(root):
        lines = row.splitlines()
        title = lines[0]
        commands = dict(line.strip().split(": ", 1) for line in lines[1:] if ": " in line)
        if "check" in commands:
            name = title.split(" (")[0]
            result.append((name, title, commands["check"], commands.get("fix", "")))
    return result


def plan(root: Path, files: list[str]) -> tuple[list[tuple[str, str, str]], list[str]]:
    """Name, check, and fix command of each check to run on the files, and the missing tools."""
    commands, missing = [], []
    for name, title, check, fix in entries(root):
        if "  MISSING" in title or "  SETUP" in title:
            if name in FILES:
                missing.append(title.strip())
            continue
        if name == "git whitespace":
            if git(root, "rev-parse", "--verify", "-q", "HEAD").returncode == 0:
                commands.append((name, check, ""))
        elif name in FILES and "{files}" in check:
            selected = [f for f in files if f.endswith(FILES[name])]
            if selected:
                names = quote(selected)
                commands.append(
                    (name, check.replace("{files}", names), fix.replace("{files}", names))
                )
    return commands, missing


def consent_command(answer: str, root: Path) -> str:
    return quote([sys.executable, str(Path(__file__).resolve()), "consent", answer, str(root)])


def stop(event: dict[str, Any]) -> dict[str, Any]:
    if event.get("stop_hook_active"):
        return {}
    root = top(str(event.get("cwd") or "."))
    if root is None:
        return {}
    files = changed(root)
    if not files:
        return {}
    path = state_path(event)
    state = load(path)
    commands, missing = plan(root, files)
    # git itself is safe to run; every other check executes the repository's tool configuration.
    tools = sorted({name for name, _, _ in commands if name != "git whitespace"})
    agreed = load(data() / "consent.json").get(str(root))
    answered = isinstance(agreed, dict) and agreed.get("tools") == tools
    if tools and not answered:
        if state.get("asked") == [str(root), tools]:
            tools = []
        else:
            state["asked"] = [str(root), tools]
            save(path, state)
            listed = "\n".join(f"$ {command}" for name, command, _ in commands)
            return {
                "decision": "block",
                "reason": (
                    "AgentFleex can check the changed files with this repository's own "
                    f"{', '.join(tools)} before you stop. Their configuration comes from the "
                    "repository and can run its code, and a tool missing locally is downloaded. "
                    "Ask the user now whether to allow these checks in this repository; do not "
                    "decide for them. Record the answer with\n"
                    f"{consent_command('yes', root)}\nor\n{consent_command('no', root)}\n"
                    f"If they agree, run the checks yourself this time:\n{listed}"
                ),
            }
    elif tools and not (isinstance(agreed, dict) and agreed.get("run")):
        tools = []
    commands = [c for c in commands if c[0] in tools or c[0] == "git whitespace"]
    mark = fingerprint(root, files) + ",".join(tools)
    if not commands or state.get("stop") == mark:
        return {}
    state["stop"] = mark
    save(path, state)

    failures = []
    for name, command, fix in commands:
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=root,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=TIMEOUT,
                check=False,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{name}: timed out after {TIMEOUT}s\n$ {command}")
            continue
        output = (result.stdout + result.stderr).strip()
        # gofmt -l lists unformatted files and still exits 0.
        if result.returncode or (name == "gofmt" and result.stdout.strip()):
            text = f"{name} failed\n$ {command}\n{output[-OUTPUT:]}"
            failures.append(text + (f"\nfix: {fix}" if fix else ""))

    if failures:
        reason = (
            "AgentFleex style checks failed on the changed files. Fix what this change introduced "
            "(use fix commands only for formatters and safe autofixes), rerun the checks, and "
            "report pre-existing failures in untouched code instead of fixing them.\n\n"
            + "\n\n".join(failures)
        )
        if missing:
            reason += "\n\nNot checked, tool not installed: " + "; ".join(missing)
        return {"decision": "block", "reason": reason}
    if missing and not state.get("missing"):
        state["missing"] = True
        save(path, state)
        return {"systemMessage": "AgentFleex skipped style checks: " + "; ".join(missing)}
    return {}


def consent(answer: str, where: str) -> int:
    """Record whether the user allows the repository's current tools to run on stop."""
    root = top(where)
    if root is None or answer not in ("yes", "no"):
        print(
            "usage: agentfleex.py consent yes|no <directory in a git repository>", file=sys.stderr
        )
        return 1
    commands, _ = plan(root, changed(root))
    tools = sorted({name for name, _, _ in commands if name != "git whitespace"})
    file = data() / "consent.json"
    agreed = load(file)
    agreed[str(root)] = {"run": answer == "yes", "tools": tools}
    save(file, agreed)
    print(
        f"agentfleex: {'allowed' if answer == 'yes' else 'declined'} {', '.join(tools)} in {root}"
    )
    return 0


def read(event: dict[str, Any]) -> dict[str, Any]:
    tool = event.get("tool_input") or {}
    if tool.get("offset") or tool.get("limit") or not tool.get("file_path"):
        return {}
    file = Path(str(event.get("cwd") or "."), str(tool["file_path"]))
    try:
        data = file.read_bytes()
    except OSError:
        return {}
    lines = data.count(b"\n") + (not data.endswith(b"\n") and bool(data))
    if lines <= LONG or b"\0" in data[:8192]:
        return {}
    path = state_path(event)
    state = load(path)
    seen = state.setdefault("reads", [])
    key = str(file.resolve())
    if key in seen:
        return {}
    outline = subprocess.run(
        [sys.executable, str(INDEX), "outline", str(file), "--root", str(file.parent)],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    rows = [line for line in outline.stdout.splitlines() if not line.startswith("#")]
    if outline.returncode or not rows:
        return {}
    seen.append(key)
    save(path, state)
    reason = (
        f"{tool['file_path']} has {lines} lines. Read only the ranges you need with offset and "
        "limit; to read the whole file anyway, repeat the same Read call. Outline "
        "(start-end kind name):\n" + "\n".join(rows)
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) == 4 and sys.argv[1] == "consent":
        return consent(sys.argv[2], sys.argv[3])
    handlers = {"stop": stop, "read": read}
    if len(sys.argv) != 2 or sys.argv[1] not in handlers:
        print(
            "usage: agentfleex.py stop|read < event.json, or consent yes|no <root>", file=sys.stderr
        )
        return 1
    try:
        event = json.load(sys.stdin)
    except ValueError as error:
        print(f"agentfleex: hook input is not JSON: {error}", file=sys.stderr)
        return 1
    print(json.dumps(handlers[sys.argv[1]](event if isinstance(event, dict) else {})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
