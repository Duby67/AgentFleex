# Rule catalog

Shared rules for `AGENTS.md`, grouped by the section they go in. Use a rule only when it holds for
the repository; replace `<...>` with verified commands and paths.

## Rules

Hard rules; stop and report instead of working around them.

- Commit, push, PR, and merge belong to the user.
- No silent fallback: fail with an actionable error.
- Secrets come from the environment; never commit or log them.
- Never report an unrun or skipped check as passed; run checks after the last change.
- Start another agent only with the user's permission.
- When docs, config, code, and tests disagree, report the contradiction instead of choosing.

## Branches

- `<develop>` is the working branch: start branches and forks from it and target every PR at it.
- `<staging>` is the test branch: `<develop>` merges into it for deployment to the test server; a
  bug found there is fixed on `<develop>` and merged again.
- `<main>`, the default branch, holds releases: only `<staging>` merges into it, after its tests
  pass.

## Work

- Make the smallest correct change. Prefer, in order: no change, existing code, the standard
  library, an installed dependency, new code. Stay in scope.
- Read narrowly: focused search, bounded reads, `git diff --stat` before diffs, quiet test output.
- For repositories with Python files, including tests, default to uv and an ignored `.venv`:
  declare dependencies in `pyproject.toml`, commit `uv.lock`, and use `uv sync`, `uv add`, and
  `uv run` instead of pip or system Python. Preserve an established environment manager unless
  the user requests migration.
- Never read or search `<generated, vendored, lockfile, snapshot, build output, and data paths>`.
- Fastest checks: `<single test command>`, `<lint changed files command>`,
  `<type check command>`.
- Do not create plan, summary, or notes files unless asked.
- Keep the repository root minimal: put a new file in an existing directory or its tool's own
  (`docs/`, `.claude/`, `.github/`); add a root file only where a tool requires it.

## Language

- Agent-facing files (`AGENTS.md`, skills, agent docs) are in English. Human docs are in
  English<, translated to: <BCP 47 codes>>; add or remove a language only when the user asks.

## Report

One line per point: result, checks run with outcome, concrete risks. Write nothing else: no empty
categories, no actions not taken (such as "not committed"), nothing the user already sees.
