# Token rules

Candidates for `AGENTS.md`. Add one only when the repository lacks it and the agent would otherwise
spend tokens; replace placeholders with verified commands and paths.

## Commands

- Exact commands for the fastest targeted check: one test file or test name, lint of changed files,
  type check. Without them the agent explores build files and runs full suites.
- Quiet flags for noisy tools (`pytest -q`, `--reporter=dot`, `--silent`), or "show only failures".

## Reading

- Read narrowly: focused search, bounded line ranges, `git diff --stat` before a full diff.
- Paths never to read or search: generated code, vendored dependencies, lockfiles, fixtures,
  snapshots, build output, large data files. Name the real paths.
- Entry points the agent would not find quickly, as one pointer each.

## Work

- Make the smallest correct change and stay in scope.
- Prefer, in order: no change, existing code, the standard library, an installed dependency, new
  code.
- Do not create plan, summary, or notes files unless asked.
- Start another agent only with the user's permission.

## Report

- One line per point: result, checks run with outcome, concrete risks. No empty categories, no
  actions not taken, nothing the user already sees.
