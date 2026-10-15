# AgentFleex

A Claude Code and Codex plugin whose skills keep AGENTS.md, repository skills, and human docs
minimal. The repository root is the plugin root, and skills live in `skills/`.

## Rules

Hard rules; stop and report instead of working around them.

- Commit, push, PR, and merge belong to the user.
- No silent fallback: fail with an actionable error.
- Secrets come from the environment; never commit or log them.
- Never report an unrun or skipped check as passed; run checks after the last change.
- Start another agent only with the user's permission.
- When docs, config, code, and tests disagree, report the contradiction instead of choosing.

## Branches

- `develop` is the working branch: start branches and forks from it and target every PR at it.
- `main`, the default branch, holds releases: only `develop` merges into it.

## Work

Make the smallest correct change. Prefer, in order: no change, existing code, the standard library,
an installed dependency, new code. Stay in scope. Read narrowly: focused search, bounded reads,
`git diff --stat` before diffs, quiet test output.

- Keep agent rules only in `AGENTS.md`; other agents' instruction files reference it.
- Keep project skills only in `skills/`; agent-specific skills paths are relative symlinks.
- Ignore local agent directories in Git; preserve `.agents/plugins/marketplace.json` as plugin
  distribution metadata.
- Keep the repository root minimal: put a new file in an existing directory or its tool's own
  (`docs/`, `.claude/`, `.github/`); add a root file only where a tool requires it.
- Use uv and the ignored `.venv` for Python, including tests; sync with `uv sync --locked`,
  add dependencies with `uv add`, and run commands with `uv run` instead of pip or system Python.
- Checks: `uv run --locked pre-commit run --all-files` and
  `uv run --locked python -m unittest discover -s tests`.
- Note changes under `## Unreleased` in `CHANGELOG.md` and its translations. Every merge into `main`
  is a release: raise `version` in both plugin manifests above the latest tag and rename that
  section to the version; CI then tags and releases it. Installed plugins update only on a new
  version.

## Language

- Agent-facing files (`AGENTS.md`, skills, agent docs) are in English. Human docs are in English,
  translated to: ru; add or remove a language only when the user asks.

## Report

One line per point: result, checks run with outcome, concrete risks. Write nothing else: no empty
categories, no actions not taken (such as "not committed"), nothing the user already sees.
