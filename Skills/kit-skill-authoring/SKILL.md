---
name: kit-skill-authoring
description: Create, split, review, or refactor repository skills shared by Codex and Claude Code. Use when changing Skills/*/SKILL.md, trigger contracts, bundled resources, agents/openai.yaml, or skill validation. Do not use for routing-only governance changes.
---

# Skill Authoring

Create focused skills that activate only for intended tasks, consume little context, and give the
agent direction rather than a script. Routing and registry wiring belong to `$kit-agent-rules`.

## Package contract

- Store skills at `Skills/<skill-name>/`; the lowercase hyphenated directory matches the
  frontmatter `name` (at most 64 characters). Codex and Claude Code read the same files through the
  `.agents/skills` and `.claude/skills` symlinks, so write for any capable agent, not for one tool.
- Frontmatter holds `name` and `description`; the only tool-specific extension is
  `disable-model-invocation: true` for a user-gated skill (Claude Code).
- Write `SKILL.md`, references, and script messages in English.
- `agents/openai.yaml` is user-facing UI metadata: keep `display_name` stable and mention
  `$skill-name` in `default_prompt`. Shared `kit-` skills keep it in English; project skills write
  `short_description` and `default_prompt` in the operator's language (Russian, as enforced by
  `Scripts/check_skills.py`).
- A user-gated skill states its explicit invocation requirement in `description`, sets
  `policy.allow_implicit_invocation: false` in `agents/openai.yaml` (Codex), and sets
  `disable-model-invocation: true` in the frontmatter (Claude Code); ordinary skills set neither.
- `$skill-name` is the repository's reference syntax for a skill in any text; it is not an
  invocation command.
- No secrets, private or absolute paths, claims about unavailable capabilities, or prose that does
  not change agent behavior.
- Stay well under 200 lines and 20,000 characters; the shortest complete skill wins.

## Shared and project ownership

Shared `kit-` skills own reusable procedures and contain no project names, paths, or domain rules.
Project adapters, named with the project prefix (for example `<project>-migrations`), supply local
context and refer to shared skills; extend the adapter instead of copying or specializing the shared
procedure. Roles and journal rules remain in `AGENTS.md`. Do not create skills for generic
reasoning, planning, or mandatory task stages. Keep a skill only when it supplies project knowledge
or reusable tools beyond ordinary agent abilities.

## What a skill contains

- **Description:** the job and project nouns first, with exact `Use when ...` and `Do not use ...`
  boundaries. This is what decides activation, and it is paid for on every request.
- **Body:** purpose, owned area, the guardrails that are actually hard, useful sources, and checks
  specific to this work. Link to canonical owners instead of copying their content.

Leave the way of researching a task and the shape of the reply to the agent. Do not add output
contracts, mandatory headings, lists of files read, or confirmations that Git actions were not
performed; `AGENTS.md` covers those once. A fixed output format belongs only where the result is
machine-read. A step-by-step procedure belongs only where the order itself is the safety property,
as in database migrations.

Keep one coherent job or risk class per skill and split only when triggers, risks, or validation
genuinely differ. Put conditional detail in one-level `references/` and deterministic logic in
`scripts/`; bundled scripts take explicit inputs, make no hidden network calls, fail non-zero with
actionable messages, and have focused tests.

## References

Consult these when a format or authoring question needs clarification, not on every task:

- [Agent Skills specification](https://agentskills.io/specification): package format and discovery.
- [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices):
  domain knowledge, concise context, progressive disclosure, and control proportional to risk.

External examples are optional guidance, not additional workflow requirements; do not install or
invoke another skill merely because an external guide recommends it.

## Checks

```text
uv run Scripts/check_skills.py Skills
uv run Scripts/check_agent_rules.py
uv run Scripts/check_docs.py
```

Sanity-check activation against a few prompts that should and should not trigger the skill, and
against adjacent skills.
