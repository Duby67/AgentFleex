---
name: fleex-skills
description: Create, split, review, or refactor repository skills shared by Codex and Claude Code. Use when changing .agents/skills/*/SKILL.md, trigger descriptions, bundled resources, or agents/openai.yaml. Do not use for AGENTS.md wiring.
---

# Skills

Create focused skills that activate only for intended tasks, consume little context, and give the
agent direction rather than a script. Wiring belongs to `$fleex-agents-md`.

## Package

- `.agents/skills/<skill-name>/SKILL.md`; the lowercase hyphenated directory matches the
  frontmatter `name` (at most 64 characters). Codex reads `.agents/skills` directly and Claude Code
  through the `.claude/skills` symlink, so write for any capable agent, not for one tool.
- Frontmatter holds `name` and `description`. A user-gated skill says so in `description`, sets
  `disable-model-invocation: true` in the frontmatter (Claude Code) and
  `policy.allow_implicit_invocation: false` in `agents/openai.yaml` (Codex).
- `agents/openai.yaml` is optional Codex UI metadata: `display_name`, `short_description`, and a
  `default_prompt` that mentions `$<skill-name>`.
- `$<skill-name>` is the reference syntax for a skill in any text, not an invocation command.
- No secrets, absolute or private paths, or claims about unavailable capabilities.
- Stay well under 200 lines; the shortest complete skill wins.

## Content

- **Description** decides activation and is paid for on every request: the job and the project
  nouns first, then exact `Use when ...` and `Do not use ...` boundaries.
- **Body:** purpose, owned area, the guardrails that are actually hard, useful sources, and checks
  specific to this work. Link to canonical owners instead of copying them.
- Leave research approach and reply shape to the agent: no output contracts, mandatory headings, or
  step lists unless the order itself is the safety property or the output is machine-read.
- One coherent job or risk class per skill; split only when triggers, risks, or checks differ.
  Conditional detail goes to one-level `references/`, deterministic logic to `scripts/` with
  explicit inputs, no hidden network calls, and actionable non-zero failures.
- Do not create skills for generic reasoning, planning, or mandatory task stages; keep a skill only
  when it adds project knowledge or tools beyond ordinary agent abilities.
- Name another skill only where its boundary with this one is easy to confuse; never list or route
  between all skills, since every named skill invites the agent to load it.

## Shared and project skills

Shared `fleex-` skills hold reusable procedures and no project names, paths, or domain rules. Project
skills use the project prefix (`<project>-<job>`), supply local context, and refer to shared skills
instead of copying them.

## Best practices

Consult when a format or design question needs it, not on every task:

- [Agent Skills specification](https://agentskills.io/specification)
- [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices)
- [Claude skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- Example skills: [anthropics/skills](https://github.com/anthropics/skills),
  [openai/skills](https://github.com/openai/skills)

External examples are guidance, not extra workflow requirements.

## Gotchas

- Claude Code-only frontmatter (`disable-model-invocation`, `paths`, `when_to_use`) is ignored by
  Codex and rejected by claude.ai and Skills API uploads; use it only for user gating.
- Claude Code cuts `description` at 1,536 characters and Codex shortens descriptions in large skill
  sets, so a trigger placed last may never be seen.

## Check

Run `scripts/check.sh` (`scripts/check.ps1` on Windows) and fix every reported error.

After a `description` change, test activation in fresh sessions: about ten prompts that should
trigger the skill and ten near-misses, including prompts for adjacent skills, each run several
times ([method](https://agentskills.io/skill-creation/optimizing-descriptions)). Keep the prompts
out of the repository.
