"""Outline the first whole-file Read of a long file, once per file and session.

Standard library only. Reads a hook event as JSON on stdin and prints a JSON reply.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

INDEX = Path(__file__).resolve().parent.parent / "skills/fleex-index/scripts/index.py"
LONG = 400


def marker(event: dict[str, Any], file: Path) -> Path:
    base = os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("PLUGIN_DATA")
    if not base:
        raise ValueError("set CLAUDE_PLUGIN_DATA or PLUGIN_DATA to a private plugin data directory")
    session = hashlib.sha256(str(event.get("session_id") or "default").encode()).hexdigest()
    name = hashlib.sha256(str(file.resolve()).encode()).hexdigest()
    return Path(base) / "reads" / session / name


def read(event: dict[str, Any]) -> dict[str, Any]:
    tool = event.get("tool_input") or {}
    if tool.get("offset") or tool.get("limit") or not tool.get("file_path"):
        return {}
    file = Path(str(event.get("cwd") or "."), str(tool["file_path"]))
    try:
        with file.open("rb") as stream:
            chunk = stream.read(8192)
            if b"\0" in chunk:
                return {}
            lines = chunk.count(b"\n")
            last = chunk[-1:]
            while chunk := stream.read(65536):
                lines += chunk.count(b"\n")
                last = chunk[-1:]
            lines += bool(last) and last != b"\n"
    except OSError:
        return {}
    if lines <= LONG:
        return {}
    path = marker(event, file)
    if path.exists():
        return {}
    outline = subprocess.run(
        [sys.executable, str(INDEX), "outline", str(file), "--root", str(file.parent)],
        capture_output=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )
    if outline.returncode:
        raise ValueError(f"outline failed for {file}: {outline.stderr.strip()}")
    rows = [line for line in outline.stdout.splitlines() if not line.startswith("#")]
    if not rows:
        return {}
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.mkdir()
    except FileExistsError:
        return {}
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
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2 or sys.argv[1] != "read":
        print("usage: agentfleex.py read < event.json", file=sys.stderr)
        return 1
    try:
        event = json.load(sys.stdin)
        print(json.dumps(read(event if isinstance(event, dict) else {})))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"agentfleex: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
