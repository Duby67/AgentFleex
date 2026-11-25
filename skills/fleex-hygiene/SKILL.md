---
name: fleex-hygiene
description: Run the repository's configured linters, formatters, type checkers, and pre-commit hooks on changed files, and set up or unify style tooling, pre-commit, uv, and .editorconfig. Use when the user asks for style checks or fixes, for a check before a PR or merge, or to set up style tooling. Do not run after every edit or response, and do not use for tests or logic review.
---

# Hygiene

Use the project's own linters, formatters, type checkers, pre-commit hooks, and CI commands.
Follow its `.editorconfig`.

Run a hygiene pass only when asked, including a requested check before a PR or merge; ordinary edits
and finished responses never trigger one. Do not repeat checks on an unchanged state.

## Find the checks

Run `scripts/checks.py` (relative to this skill's directory) from anywhere in the repository with
Python 3.9+. It reads configuration only and prints each configured tool with its check
and fix commands, run through the project environment (`uv run`, `poetry run`, `.venv`, `npx`, the
lockfile's package manager) or, for a Python tool the project does not install, `uvx` at a pinned
version, and the CI commands that run them. `{files}` stands for the changed files: `git diff
--name-only HEAD` plus new untracked files, filtered to what the tool handles. When CI runs a tool
differently, CI's invocation wins. A tool pre-commit runs is checked only through it.

## Apply

Repository configuration can execute code; the user's request authorizes the requested checks,
subject to the client's normal execution approvals.

- Run the check commands on changed files; run project-wide commands (`tsc`, `go vet`, `mypy`
  without files) once.
- Use fix commands only for formatters and safe autofixes, then rerun the checks; fix the rest by
  hand.
- Never change tool configuration, write a default into the repository, or silence a rule (`noqa`,
  `eslint-disable`, `type: ignore`) to pass, unless the user asks; a rule that looks wrong is
  reported instead.
- Editor diagnostics (such as a VS Code diagnostics tool) cover only open or saved files, so an
  empty result is not a pass; confirm with the configured tool's command line.
- Leave pre-existing failures in untouched code alone and report them separately.
- A line marked `MISSING` names a tool to install; `SETUP` gives the command that installs the
  project environment. Tell the user once, never install on your own, and run the remaining checks.

To set up or unify tooling, pre-commit, uv, or `.editorconfig`, follow
[the setup guide](references/setup.md).

## Check

`git diff --check HEAD` passes, and every listed check passes on the changed files or its failure is
reported with output.
