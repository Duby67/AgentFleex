"""Install the versioned Git hooks by pointing core.hooksPath at .githooks."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = ".githooks"
HOOKS_DIR = ROOT / HOOKS_PATH
PRE_PUSH_HOOK = HOOKS_DIR / "pre-push"


class HookSetupError(RuntimeError):
    """Raised when the repository hook contract cannot be installed safely."""


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        diagnostic = result.stderr.strip() or "git command failed"
        raise HookSetupError(diagnostic)
    return result.stdout.strip()


def _validate_hook() -> None:
    if HOOKS_DIR.is_symlink() or not HOOKS_DIR.is_dir():
        raise HookSetupError(f"{HOOKS_PATH}: hooks directory is missing or is a symlink")
    if PRE_PUSH_HOOK.is_symlink() or not PRE_PUSH_HOOK.is_file():
        raise HookSetupError(f"{HOOKS_PATH}/pre-push: hook is missing or is a symlink")

    hook_content = PRE_PUSH_HOOK.read_bytes()
    if not hook_content.startswith(b"#!/usr/bin/env bash\n") or b"\r\n" in hook_content:
        raise HookSetupError(f"{HOOKS_PATH}/pre-push: hook must use a Bash shebang and LF endings")

    mode = PRE_PUSH_HOOK.stat().st_mode
    PRE_PUSH_HOOK.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if not os.access(PRE_PUSH_HOOK, os.X_OK):
        raise HookSetupError(f"{HOOKS_PATH}/pre-push: hook is not executable")


def main() -> int:
    try:
        repository_root = Path(_run_git("rev-parse", "--show-toplevel")).resolve()
        if repository_root != ROOT:
            raise HookSetupError("setup script is not located in the active repository root")
        _validate_hook()
        _run_git("config", "--local", "core.hooksPath", HOOKS_PATH)
        configured_path = _run_git("config", "--local", "--get", "core.hooksPath")
        if configured_path != HOOKS_PATH:
            raise HookSetupError("core.hooksPath verification failed")
    except HookSetupError as exc:
        print(f"Git hook setup failed: {exc}", file=sys.stderr)
        return 1

    print(f"Git hooks configured: core.hooksPath={HOOKS_PATH} pre-push=executable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
