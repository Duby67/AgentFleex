---
name: fleex-hygiene
description: Keep changes in the repository's single style by finding and running its configured linters, formatters, type checkers, pre-commit hooks, and CI style steps. Use when finishing a code change, fixing lint, format, or type failures, or setting up or unifying style tooling. Do not use for writing or running tests, or for reviewing logic.
---

# Hygiene

The repository's own configuration is the single style: its linter, formatter, and type checker
configs, `.editorconfig`, pre-commit hooks, and what CI runs. Match it; do not bring another.

## Find the checks

Run `scripts/checks.py` (relative to this skill's directory) from anywhere in the repository with
Python 3.8+. It reads configuration only and prints each configured tool with its check and fix
commands, run through the project environment (`uv run`, `poetry run`, `.venv`, `npx`, the
lockfile's package manager). `{files}` stands for the changed files: `git diff --name-only HEAD`
plus new untracked files, filtered to what the tool handles. When CI runs a tool differently, CI's
invocation wins.

## Apply

- Run the check commands on changed files; run project-wide commands (`tsc`, `go vet`, `mypy`
  without files) once.
- Use fix commands only for formatters and safe autofixes, then rerun the checks; fix the rest by
  hand.
- Never change tool configuration, add a tool, or silence a rule (`noqa`, `eslint-disable`,
  `type: ignore`) to pass, unless the user asks; a rule that looks wrong is reported instead.
- Leave pre-existing failures in untouched code alone and report them separately.
- A line marked `MISSING` names what to install; when `uv run`, `poetry run`, or `npx` cannot find a
  tool, the project environment is not installed (`uv sync`, `poetry install`, `npm install`). Tell
  the user once and run the remaining checks.

## Setting up

When asked to add or unify tooling, propose one formatter and one linter per language, configured
in an existing file (`pyproject.toml`, `package.json`) where possible, and matching `.editorconfig`
and CI; apply it only after the user agrees. Reformatting a whole repository is a separate change.

## Check

`git diff --check HEAD` passes, and every listed check passes on the changed files or its failure is
reported with output.
