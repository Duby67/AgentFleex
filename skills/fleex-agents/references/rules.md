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

## Work

- Make the smallest correct change. Prefer, in order: no change, existing code, the standard
  library, an installed dependency, new code. Stay in scope.
- Read narrowly: focused search, bounded reads, `git diff --stat` before diffs, quiet test output.
- Never read or search `<generated, vendored, lockfile, snapshot, build output, and data paths>`.
- Fastest checks: `<single test command>`, `<lint changed files command>`,
  `<type check command>`.
- Do not create plan, summary, or notes files unless asked.

## Language

- Agent-facing files (`AGENTS.md`, skills, agent docs) are in English. Human docs are in
  <language, English by default>; change it only when the user asks.

## Report

One line per point: result, checks run with outcome, concrete risks. Write nothing else: no empty
categories, no actions not taken (such as "not committed"), nothing the user already sees.
