---
name: fleex-agents-md
description: Wire AGENTS.md, CLAUDE.md, and repository skills together and create AGENTS.md from the starter template. Use when creating AGENTS.md, changing CLAUDE.md, or wiring a skill addition, rename, split, or removal into the repository. Do not use for optimizing AGENTS.md content, writing skill content, or human-facing documentation.
---

# AGENTS.md wiring

These rules apply to the repository being worked on. The content of `AGENTS.md` belongs to
`$fleex-agents-optimize`; skill content belongs to `$fleex-skills`.

## Wiring

- `AGENTS.md` is the single rules file. Codex reads it natively; `CLAUDE.md` holds one line,
  `@AGENTS.md`, so Claude Code imports the same file.
- `.agents/skills/` is the only source of project skills; Codex reads it natively. `.claude/skills`
  is a relative symlink to it for Claude Code and never holds files of its own.
- Shared `fleex-` skills come from the AgentFleex plugin; never copy them into the repository.
- Both clients discover skills from their `description` fields; a routing table in `AGENTS.md` is
  not needed and duplicates those descriptions.
- A skill rename, split, or removal updates `.agents/skills/` and every reference in one change,
  without aliases.

## New AGENTS.md

A repository without `AGENTS.md` starts from `assets/AGENTS.template.md`: fill in the project
sentence, keep only the rules that hold for this repository, then apply `$fleex-agents-optimize`.

## Gotchas

- A rename or move also appears in `.gitignore` comments and `agents/openai.yaml`; search for the
  old name across the repository, not only in Markdown.

## Check

From the repository root, run `../fleex-skills/scripts/check.sh` relative to this skill's directory
(`check.ps1` on Windows) and fix every reported error.
