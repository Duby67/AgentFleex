# AgentFleex

AgentFleex helps Claude Code and Codex agents navigate code and maintain repository rules, skills,
documentation, checks, and release workflows.

## Philosophy

Review every existing and proposed feature against five criteria:

- Does it reduce token consumption?
- Does it reduce the number of actions an agent takes?
- Does it prevent repeated work?
- Does it simplify repository organization?
- Is the effort to maintain it proportionate to its benefits?

Use the answers to decide what to add, keep, simplify, or remove. Share organization principles
across projects and choose files and workflows for each project's needs.

## AgentFleex repository

| Area | Role |
| --- | --- |
| Project | The repository's own rules, configuration, and documentation, including `AGENTS.md`, `README.md`, and `docs/`. |
| Tests and benchmarks | Tests in `tests/` verify behavior. Future benchmarks will measure how features affect agent work, including token consumption and action counts. |
| Plugin | The repository's main product for Claude Code and Codex, with its skills in `skills/`, hooks in `hooks/`, and client distribution metadata. |

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

## Skills

Both clients find a skill by its `description`, which goes into every request; the body and its
references are read only when the skill is used. Skills marked explicit run only as
`$<skill>` (Codex) or `/<skill>` (Claude Code), so their descriptions cost no context.

| Skill | Owns | Invocation |
| --- | --- | --- |
| [fleex-agents](./skills/fleex-agents/SKILL.md) | `AGENTS.md`, `.claude/CLAUDE.md`, and the [catalog of shared rules](./skills/fleex-agents/references/rules.md) | automatic |
| [fleex-skills](./skills/fleex-skills/SKILL.md) | Project skills, their wiring, and links to best practices | automatic |
| [fleex-docs](./skills/fleex-docs/SKILL.md) | Human docs and the [backlog](./skills/fleex-docs/references/todo.md) | automatic |
| [fleex-hygiene](./skills/fleex-hygiene/SKILL.md) | Linters, formatters, type checkers, pre-commit, uv, `.editorconfig` | automatic, on request or before a PR |
| [fleex-index](./skills/fleex-index/SKILL.md) | A dependency-free navigation script: map, outline, show, find, refs | automatic |
| [fleex-repo](./skills/fleex-repo/SKILL.md) | Audit and setup of Git and GitHub files and settings, and the release mechanism | explicit |

Use the project's configured checks at the pre-commit and CI checkpoints.

## Layout for repositories configured by AgentFleex

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | The single rules file and the only entry point; Codex reads it natively |
| `.claude/CLAUDE.md` | Claude Code only: one line, `@../AGENTS.md`, imports the same file |
| `skills/` | Project skills, when they exist; `.agents/skills` and `.claude/skills` are relative symlinks to it, only for agents in use |
| Repository root | Keep tool-required files at the root. Choose a license if the project needs one. |
| `docs/` | Human documentation, with security and contributing guides as needed. |
| `.github/` | GitHub workflows and concise issue and PR templates tailored to the project. |

Agent directories (`.claude/`, `.cursor/`) are created only for agents in use and ignored by Git;
required plugin distribution metadata stays tracked through an explicit exception. Shared `fleex-*`
skills come from the plugin and are not copied into the repository.

Write documentation in English. Add a security policy for a public project when the request covers
public maintenance or vulnerability reporting. Add a contributing guide when the request covers
collaboration by multiple contributors. Configure Dependabot only by explicit request.

## Branches and releases

AgentFleex uses `develop` as the working branch and `main` for releases. Pull requests into
`develop` are squash-merged. Pre-commit gates the test matrix on these pull requests.
Releases merge from `develop` into `main` with a merge commit.

Every merge into `main` is a release with a new Semantic Versioning version: CI checks the version
and changelogs, tags the version, and publishes a GitHub release with notes from
`docs/CHANGELOG.md`.

## Hooks

The plugin ships only a `PreToolUse` hook matching Claude Code's `Read` tool. The first whole read
of a file over 400 lines is denied with its fleex-index outline; repeating the read allows the
whole file. Ranged reads and short or binary files pass through. Line counting uses bounded
buffers, and atomic markers prevent repeated denials when reads run concurrently.

Hooks need `python3` or `python` on `PATH` and `CLAUDE_PLUGIN_DATA` or `PLUGIN_DATA` pointing to
a private plugin data directory. There is no shared temporary-directory fallback. Codex must trust
plugin hooks in `/hooks`, but this matcher does not intercept shell commands or other read tools.

## Saving tokens

The main cost is what goes into every request: `AGENTS.md` and skill descriptions. `AGENTS.md`
holds only what every task needs and the agent cannot infer; rare tasks live in skill references
or in explicit skills; every fact lives in one place, and everything else links to it. Rules once
written into a repository's `AGENTS.md` belong to its owner and are not synced with the catalog.

## Contributing

Development setup, checks, branches, pull requests, and releases:
[CONTRIBUTING.md](docs/CONTRIBUTING.md). Security reports: [SECURITY.md](docs/SECURITY.md).
Licensed under [MIT](./LICENSE).

## References

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: memory](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Skills: [specification](https://agentskills.io/specification),
  [best practices](https://agentskills.io/skill-creation/best-practices),
  [Anthropic examples](https://github.com/anthropics/skills), [OpenAI examples](https://github.com/openai/skills)
