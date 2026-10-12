---
name: fleex-skills
description: Create, split, rename, remove, review, or refactor repository skills shared by Codex and Claude Code, and wire them into a top-level skills directory, .agents/skills, .claude/skills, or .cursor/skills. Use when changing a project skill's SKILL.md, trigger descriptions, bundled resources, agents/openai.yaml, or the skills symlinks. Do not use for AGENTS.md or CLAUDE.md.
---

# Skills

Create focused skills that activate only for intended tasks, consume little context, and give the
agent direction rather than a script.

## Wiring

- Project skills live only in the repository's top-level `skills/`, when present. Move existing
  skills there; never copy them between paths.
- Every local agent skills path (`.<agent>/skills`) is a relative symlink `../skills` to the
  repository's root `skills/`, including paths for agents added later. Codex reads
  only `.agents/skills`, Claude Code only `.claude/skills`, and Cursor `.agents/skills`,
  `.cursor/skills`, and `.claude/skills`.
- An agent is in use when it is the client you run in, its directory holds local files beyond
  committed plugin metadata, or the user says so; create an agent's directory only then.
- Ignore local agent directories (`.agents/`, `.claude/`, `.cursor/`, and other agents in use)
  in `.gitignore`; keep local symlinks on disk, outside Git. Preserve an explicit exception for
  plugin distribution metadata when the repository ships it.
- Shared `fleex-` skills come from the AgentFleex plugin; never copy them into the repository.
- A rename, split, or removal updates the source directory and every reference in one change,
  without aliases; search the whole repository, including `.gitignore` comments and
  `agents/openai.yaml`.

## Package

- `<source>/<skill-name>/SKILL.md`; the lowercase hyphenated directory matches the frontmatter
  `name` (at most 64 characters). Several agents may read the same skill, so write for any capable
  agent, not for one tool.
- Frontmatter holds `name` and `description`. A user-gated skill says so in `description`, sets
  `disable-model-invocation: true` in the frontmatter (Claude Code) and
  `policy.allow_implicit_invocation: false` in `agents/openai.yaml` (Codex).
- `agents/openai.yaml` is optional Codex UI metadata: `display_name`, `short_description`, and a
  `default_prompt` that mentions `$<skill-name>`.
- `$<skill-name>` is the reference syntax for a skill in any text, not an invocation command.
- Write skills in English.
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

Shared `fleex-` skills ship in the AgentFleex plugin and hold reusable procedures with no project
names, paths, or domain rules. Project skills live in the source directory, use the project prefix
(`<project>-<job>`), supply local context, and refer to shared skills instead of copying them.

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
- Cursor also loads `.claude/skills`, so a repository with both `.agents/skills` and
  `.claude/skills` may show each skill twice in Cursor; check its skill list.
- Claude Code cuts `description` at 1,536 characters and Codex shortens descriptions in large skill
  sets, so a trigger placed last may never be seen.

## Check

From the repository root, run `scripts/check.sh` relative to this skill's directory
(`scripts/check.ps1` on Windows) and fix every reported error.

After a `description` change, test activation in fresh sessions: about ten prompts that should
trigger the skill and ten near-misses, including prompts for adjacent skills, each run several
times ([method](https://agentskills.io/skill-creation/optimizing-descriptions)). Keep the prompts
out of the repository.
