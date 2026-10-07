# AgentFleex

A template for agent-driven repositories.

## Rules

Hard rules; stop and report instead of working around them.

- Commit, push, PR, and merge belong to the developer.
- No silent fallback: fail with an actionable error.
- Secrets come from the environment; never commit or log them.
- Never report an unrun or skipped check as passed; run checks after the last change.
- Start another agent only with the operator's permission.
- When docs, config, code, and tests disagree, report the contradiction instead of choosing.

## Work

Make the smallest correct change. Prefer, in order: no change, existing code, the standard library,
an installed dependency, new code. Stay in scope. Read narrowly: focused search, bounded reads,
`git diff --stat` before diffs, quiet test output.

## Report

One line per point: result, checks run with outcome, concrete risks. Write nothing else: no empty
categories, no actions not taken (such as "not committed"), nothing the user already sees.
