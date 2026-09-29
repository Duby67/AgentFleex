---
name: kit-docs
description: Synchronize human-facing Markdown with behavior verified in code, tests, configuration, or workflows. Use when editing README.md, Docs/*.md, Tests/README.md, or TODO.md. Do not use for AGENTS.md or skills.
---

# Documentation

Keep human-facing documentation true to current behavior, concise, in the documentation language
set in `AGENTS.md`, and with each fact in exactly one canonical owner (the sources-of-truth table in
`AGENTS.md`; navigation lives in `README.md` and `Docs/README.md`, backlog in `TODO.md`).

## Principles

- Confirm a claim from the smallest source that proves it: code, tests, configuration, or workflows.
  `TODO.md` is never a behavior source.
- Update the owner and only the links or one-line summaries that point to it; do not restate another
  document's area.
- Document stable contracts. Call sequences and similar details that change often are proven by
  code and tests, not prose.
- Rollout- or migration-specific instructions are temporary: remove them once the cutover is
  confirmed; Git keeps the history. Remove a closed `TODO.md` item only when its result is recorded
  in the canonical owner.
- If the text exposes a defect in code or configuration, verify the intended behavior and fix it only
  within the authorized scope.

## Guardrails

Do not copy secrets or real identifiers, create historical drafts, or change code merely to match
text. Changes beyond documentation require authorization within the task and their own checks.

## Checks

Run `uv run Scripts/check_docs.py`; it verifies referenced paths, links, skill references, and
navigation. A pure documentation diff does not need the code test suite.
