# AgentFleex

A Claude Code and Codex plugin that keeps `AGENTS.md`, repository skills, and documentation short
and consistent.

## Installation

Claude Code:

```bash
claude plugin marketplace add Duby67/AgentFleex
claude plugin install agentfleex@agentfleex
```

Codex:

```bash
codex plugin marketplace add Duby67/AgentFleex
codex plugin add agentfleex@agentfleex
```

## What the plugin sets up in a repository

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | The single rules file; Codex reads it natively |
| `CLAUDE.md` | One line, `@AGENTS.md`: Claude Code imports the same file |
| `.agents/skills/` | The only source of project skills; Codex reads it natively |
| `.claude/skills` | Relative symlink to `.agents/skills/` for Claude Code |

Shared `fleex-*` skills come from the plugin and are not copied into the repository. Both clients
find skills by their `description` field, so `AGENTS.md` needs no routing table.

Agent-facing files (`AGENTS.md`, skills, agent docs) are written in English. Human docs are in the
language set in `AGENTS.md`: the agent asks for it when it creates `AGENTS.md` (English by default)
and changes it only when the user asks. In chat the agent replies in the language of the question.

## Repository layout

The repository root is the plugin root; skills live in `skills/`. Manifests: `.claude-plugin/` and
`.codex-plugin/` (plugin), `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`
(marketplaces). To try skill changes, start Claude Code with `claude --plugin-dir .`; in Codex,
reinstall the plugin from the local marketplace.

## Saving tokens

The main cost is files the agent reads often, above all `AGENTS.md`, which goes into every model
request. Therefore:

- `AGENTS.md` holds only what every task needs and the agent cannot infer: what the project is,
  hard invariants, pointers to owners;
- anything the file already implies or the agent already knows is removed;
- task details live in skills: only their `description` goes into every request, and the body is
  read on demand;
- every fact lives in one place, and everything else links to it.

Each skill owns its files: [fleex-agents](./skills/fleex-agents/SKILL.md) owns `AGENTS.md`,
`CLAUDE.md`, and the single catalog of shared rules; [fleex-skills](./skills/fleex-skills/SKILL.md)
owns skills, their wiring, and links to best practices; [fleex-docs](./skills/fleex-docs/SKILL.md)
owns human documentation. Rules once written into a repository's `AGENTS.md` belong to its owner and
are not synced with the catalog.

## References

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: memory](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Skills: [specification](https://agentskills.io/specification),
  [best practices](https://agentskills.io/skill-creation/best-practices),
  [Anthropic examples](https://github.com/anthropics/skills), [OpenAI examples](https://github.com/openai/skills)
