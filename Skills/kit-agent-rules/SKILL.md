---
name: kit-agent-rules
description: Keep agent rules consistent across AGENTS.md, task routing, the skill registry, process links, and their validation. Use when changing AGENTS.md, Docs/GIT_WORKFLOW.md process policy, Scripts/check_agent_rules.py, or wiring an already-authored skill addition, rename, split, move, or removal into the repository. Do not use for writing skill content or human-facing documentation.
---

# Agent Rules

Keep task routing, repository skills, and their validation consistent without changing product
behavior. Skill content quality belongs to `$kit-skill-authoring`.

## Scope

- `AGENTS.md`: the repository router, always loaded by Codex and imported by `CLAUDE.md` (a single
  `@AGENTS.md` line) for Claude Code; rules every task must follow belong here, not in an on-demand
  skill;
- `.agents/`: only the Codex discovery symlink and the local, git-ignored session files
  `.agents/tasks.md` and `.agents/handoff.md`; `AGENTS.md` owns their protocol;
- `Skills/**` structure and routing. `Skills/` is the only skill source; `.agents/skills` (Codex)
  and `.claude/skills` (Claude Code) are relative symlinks to it and never hold files of their own;
- `Docs/GIT_WORKFLOW.md` process policy and `Docs/README.md` navigation;
- `Scripts/check_agent_rules.py`, `Scripts/check_skills.py`, and `.githooks/`.

## Principles

- Every rule has one canonical owner; other places link to it instead of copying it.
- Hard rules (protected branches, secrets, privacy, no silent fallback, no delegation, honest
  evidence) are stated imperatively. Soft guidance (what to read, which checks to run, how to reply)
  gives direction and a quality bar, not an algorithm.
- `AGENTS.md` is paid for on every model request: keep it short, and move detail that only some
  tasks need into a skill or a canonical document.
- A skill rename, split, or removal updates `Skills/`, the `AGENTS.md` route, and process links in
  one change, without compatibility aliases.
- Names and paths describe the job, not a tool: no agent-, model-, or vendor-specific words in skill
  names.
- Never weaken protected-branch or commit, push, PR, and merge restrictions.

## Validation contract

`Scripts/check_agent_rules.py` checks that every skill is routed from `AGENTS.md` and that
`AGENTS.md` stays English. `Scripts/check_docs.py` owns path, link, `$skill` reference, and
navigation integrity. `Scripts/check_skills.py` owns package validation: frontmatter, naming,
language, UI metadata, size, and links. Do not add checks that require specific prose; they freeze
wording instead of protecting meaning.

```text
uv run Scripts/check_skills.py Skills
uv run Scripts/check_agent_rules.py
uv run Scripts/check_docs.py
```

Run the checker tests when validation logic changes.
