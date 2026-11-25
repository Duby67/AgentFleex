---
name: fleex-skills
description: Wire project skills into Claude Code, Codex, or Cursor and validate shared skill packages. Use when adding, moving, or removing skills that need to be discovered across these clients.
---

# Shared skills

Keep one source for project skills. Preserve a working layout and use the client's skill authoring
guidance for package content. When setting up AgentFleex's shared layout, put project skills in
`skills/` and link each client in use to it with a relative `../skills` symlink.

- Use `.agents/skills` for Codex and `.claude/skills` for Claude Code. For Cursor, reuse a supported
  path already present so it does not discover duplicates.
- Keep local wiring out of Git and preserve tracked plugin distribution metadata.
- Reference shared `fleex-*` skills from the plugin. When moving or deleting a skill, update
  its references and discovery paths together.
- For explicit-only skills, set `disable-model-invocation: true` in Claude Code frontmatter and
  `policy.allow_implicit_invocation: false` in Codex's `agents/openai.yaml`.

Validate discovery and references for the clients affected by the change. For the AgentFleex
layout, run `scripts/check.sh` or `scripts/check.ps1` from the target repository root. When trigger
behavior changes, try representative requests and near misses.
