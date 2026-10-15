---
name: fleex-docs
description: Synchronize human-facing Markdown with behavior verified in code, tests, configuration, or workflows, and, only on request, translate it under docs/<code>/. Use when editing README.md, TODO.md, or other human documentation, including recording findings or tasks in the TODO.md backlog, or when the user asks for a translation pass or to add or remove a language. Do not use for AGENTS.md or skills.
---

# Docs

Keep human documentation true to current behavior, concise, and with each fact in exactly one
canonical owner.

- Confirm a claim from the smallest source that proves it: code, tests, configuration, or
  workflows. A backlog is never a behavior source.
- Update the owner and only the links or one-line summaries that point to it.
- Document stable contracts; details that change often are proven by code and tests, not prose.
- Remove rollout- or migration-specific instructions once the cutover is confirmed; Git keeps the
  history.
- If the text exposes a defect in code or configuration, report it; fix it only within the
  authorized scope.
- Do not copy secrets or real identifiers, keep historical drafts, or change code to match text.
- `TODO.md` is the backlog of known defects, risks, and planned work: follow
  [the backlog guide](references/todo.md).

## Translations

Write human docs in English. Translations may lag during development: when an English source
changes, put a note under the switcher of each existing translation, in its language, linking the
original (`> Перевод отстаёт от [английской версии](../../README.md).`), and keep switchers linked
to existing files. Translate, or add or remove a language, only when the user asks, including a
pass before a PR; then follow [the translation guide](references/i18n.md).

## Check

From the repository root, run `../fleex-skills/scripts/check.sh` relative to this skill's directory
(`check.ps1` on Windows) to verify links and translations, and confirm by hand that referenced paths
in code spans exist.
