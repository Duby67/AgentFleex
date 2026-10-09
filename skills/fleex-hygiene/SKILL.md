---
name: fleex-hygiene
description: Keep changes in the repository's single style by finding and running its configured linters, formatters, type checkers, pre-commit hooks, and CI style steps, with plugin defaults where none are configured. Use when finishing a code change, fixing lint, format, or type failures, or setting up or unifying style tooling. Do not use for writing or running tests, or for reviewing logic.
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

When asked to add or unify tooling, start from the plugin defaults: copy their settings into an
existing file (`pyproject.toml`, `package.json`) where possible, so the repository no longer depends
on the plugin, and match `.editorconfig` and CI; apply it only after the user agrees. Reformatting a
whole repository is a separate change.

## Check

`git diff --check HEAD` passes, and every listed check passes on the changed files or its failure is
reported with output.
