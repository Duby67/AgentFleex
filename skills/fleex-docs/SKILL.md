---
name: fleex-docs
description: Maintain human-facing Markdown using verified project behavior. Use for README, TODO, and other human documentation. Do not use for AGENTS.md or skills.
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

Write documentation in English and follow the repository’s existing language policy.

## Check

From the repository root, run `../fleex-skills/scripts/check.sh` relative to this skill's directory
(`check.ps1` on Windows) to verify links, and confirm by hand that referenced paths
in code spans exist.
