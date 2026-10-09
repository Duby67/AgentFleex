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

## Work

Make the smallest correct change. Prefer, in order: no change, existing code, the standard library,
an installed dependency, new code. Stay in scope. Read narrowly: focused search, bounded reads,
`git diff --stat` before diffs, quiet test output.

## Language

- Agent-facing files (`AGENTS.md`, skills, agent docs) and human docs are in English; change the
  human docs language only when the user asks.

## Report

One line per point: result, checks run with outcome, concrete risks. Write nothing else: no empty
categories, no actions not taken (such as "not committed"), nothing the user already sees.
