---
name: fleex-agents-md
description: Keep AGENTS.md minimal and consistent with the repository skills and docs. Use when changing AGENTS.md or CLAUDE.md, or wiring a skill addition, rename, split, or removal into the repository. Do not use for writing skill content or human-facing documentation.
---

# AGENTS.md

`AGENTS.md` is read on every model request, so every line costs tokens on every task. Skill content
quality belongs to `$fleex-skills`. These rules apply to the repository being worked on.

## Wiring

- `AGENTS.md` is the single rules file. Codex reads it natively; `CLAUDE.md` holds one line,
  `@AGENTS.md`, so Claude Code imports the same file.
- `.agents/skills/` is the only source of project skills; Codex reads it natively. `.claude/skills`
  is a relative symlink to it for Claude Code and never holds files of its own.
- Shared `fleex-` skills come from the AgentFleex plugin; never copy them into the repository.
- Both clients discover skills from their `description` fields; a routing table in `AGENTS.md` is
  not needed and duplicates those descriptions.

## What belongs in AGENTS.md

A repository without `AGENTS.md` starts from `assets/AGENTS.template.md`: fill in the project
sentence, then keep only the rules that hold for this repository.

Keep only what every task needs and the agent cannot infer:

- one or two sentences on what the project is and is not;
- hard invariants whose violation is costly (data, money, security, privacy, protected branches);
- pointers to canonical owners the agent would not find on its own.

Remove or move out:

- statements the file already implies ("this file is for agents", "write this file in English");
- general engineering advice any capable agent already follows;
- task-specific procedures (move to a skill) and human-facing explanations (move to docs);
- copies of facts owned elsewhere (link instead);
- examples, history, and rationale that do not change behavior.

State hard rules imperatively; give soft guidance as direction, not an algorithm. A skill rename,
split, or removal updates `.agents/skills/` and every reference in one change, without aliases.

## Gotchas

- A line describing the file itself ("it is loaded on every request", "this file is for agents") is
  noise even inside a rule; keep only the rule.
- A rename or move also appears in `.gitignore` comments and `agents/openai.yaml`; search for the
  old name across the repository, not only in Markdown.

## Check

Re-read the diff and ask for each added line whether an agent would act differently without it; if
not, delete it. From the repository root, run `../fleex-skills/scripts/check.sh` relative to this
skill's directory (`check.ps1` on Windows) and fix every reported error.
