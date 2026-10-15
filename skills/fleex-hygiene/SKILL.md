---
name: fleex-hygiene
description: User-invoked repository linting, formatting, type checks, and style tooling setup. Use only when the user requests these checks, fixes, or setup, including a requested check before a PR or merge. Do not invoke automatically after edits or at the end of a response. Do not use for tests or logic review.
disable-model-invocation: true
---

# Hygiene

The repository's own configuration is the single style: its linter, formatter, and type checker
configs, `.editorconfig`, pre-commit hooks, and what CI runs. Where it configures no tool for a role
(Python style, Python types, shell), the plugin defaults in `assets/` apply: Ruff with
`assets/ruff.toml`, mypy with `assets/mypy.ini`, and ShellCheck's built-in rules. An existing
configuration always wins over a default.

## Find the checks

Run `scripts/checks.py` (relative to this skill's directory) from anywhere in the repository with
Python 3.9+. It reads configuration only and prints each configured or default tool with its check
and fix commands, run through the project environment (`uv run`, `poetry run`, `.venv`, `npx`, the
lockfile's package manager) or, for a Python tool the project does not install, `uvx`, and the CI
commands that run them in GitHub Actions, GitLab, CircleCI, Azure, Bitbucket, Travis, Drone,
Woodpecker, Buildkite, and Jenkins. `{files}` stands for the changed files: `git diff --name-only
HEAD` plus new untracked files, filtered to what the tool handles. When CI runs a tool differently,
CI's invocation wins.

## Apply

Run this skill only on request. A requested PR or merge check is a suitable checkpoint; ordinary
edits and completed responses do not trigger a hygiene pass. Honor explicit repository checks
without loading this skill on every edit. Use the existing pre-commit and CI checks when available;
do not repeat checks on an unchanged state. Repository configuration can execute code; the user's
request authorizes the requested checks, subject to the client's normal execution approvals.

- Run the check commands on changed files; run project-wide commands (`tsc`, `go vet`, `mypy`
  without files) once.
- Use fix commands only for formatters and safe autofixes, then rerun the checks; fix the rest by
  hand.
- Never change tool configuration, write a default into the repository, or silence a rule (`noqa`,
  `eslint-disable`, `type: ignore`) to pass, unless the user asks; a rule that looks wrong is
  reported instead.
- When the client exposes editor diagnostics (such as a VS Code diagnostics tool), read them for the
  changed files too. Extensions often analyze only open or saved files, so an empty result is not a
  pass and a reported line may be stale; confirm with the tool's command line when you can.
  Diagnostics from tools the repository does not configure come from the user's editor settings: fix
  them when the fix keeps behavior, and suggest committing that tool's configuration so editor,
  command line, and CI agree.
- Leave pre-existing failures in untouched code alone and report them separately.
- A line marked `MISSING` names a tool to install; `SETUP` gives the command that installs the
  project environment. Tell the user once, never install on your own, and run the remaining checks.

## Setting up

When setting up Python tooling, including a repository with only Python tests, default to a
non-packaged uv project (`[tool.uv] package = false`) unless it builds a Python distribution.
Keep dependencies in `pyproject.toml`, commit `uv.lock`, ignore `.venv/`, and create it with
`uv sync`. Add development tools with `uv add --dev`; run tests and tools with `uv run --locked`.
Preserve an established environment manager unless the user requests migration.

Every repository runs its hygiene checks through pre-commit: `.pre-commit-config.yaml` lists the
linters, formatters, type checkers, and file checks (whitespace, end of file, merge conflicts,
YAML, JSON) with `rev` pinned to a commit, CI runs `pre-commit run --all-files`, and contributors
install it once with `uv run --locked pre-commit install` in a uv project, or
`uvx pre-commit install` otherwise. A tool pre-commit runs is checked only through it.
When a repository has no such file, propose one built from its existing tools and CI steps.

When asked to add or unify tooling, start from the plugin defaults: copy their settings into an
existing file (`pyproject.toml`, `package.json`) where possible, so the repository no longer depends
on the plugin, and match `.editorconfig` and CI; apply it only after the user agrees. Reformatting a
whole repository is a separate change.

## Check

`git diff --check HEAD` passes, and every listed check passes on the changed files or its failure is
reported with output.
