# AgentFleex

**English** · [Русский](docs/ru/README.md)

A Claude Code and Codex plugin that configures repositories one way: agent rules, skills, docs and
translations, style checks, GitHub files and settings, and releases, with cheap code navigation for
the agent.

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
| [fleex-docs](./skills/fleex-docs/SKILL.md) | Human docs, [translations](./skills/fleex-docs/references/i18n.md), and the [`TODO.md` backlog](./skills/fleex-docs/references/todo.md) | automatic; translations on request |
| [fleex-hygiene](./skills/fleex-hygiene/SKILL.md) | Linters, formatters, type checkers, pre-commit, uv, `.editorconfig` | automatic, on request or before a PR |
| [fleex-index](./skills/fleex-index/SKILL.md) | A dependency-free navigation script: map, outline, show, find, refs | automatic |
| [fleex-repo](./skills/fleex-repo/SKILL.md) | Audit and setup of Git and GitHub files and settings, and the release mechanism | explicit |
| [fleex-vscode](./skills/fleex-vscode/SKILL.md) | The project's ignored `.vscode/` | explicit |

Checks and translations never run after every edit or response; pre-commit and CI remain the
validation checkpoints. Existing configuration always wins over the plugin's defaults.

## Repository layout

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | The single rules file and the only entry point; Codex reads it natively |
| `.claude/CLAUDE.md` | Claude Code only: one line, `@../AGENTS.md`, imports the same file |
| `skills/` | Project skills, when they exist; `.agents/skills` and `.claude/skills` are relative symlinks to it, only for agents in use |
| `README.md`, `LICENSE`, `.gitignore`, `.gitattributes`, `.editorconfig`, `.pre-commit-config.yaml` | The only root files besides package manifests |
| `docs/` | Human docs: `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `TODO.md`, and translations under `docs/<code>/` |
| `.github/` | Issue forms, the PR template, Dependabot, CI, and the release script |

Agent directories (`.claude/`, `.cursor/`) are created only for agents in use and ignored by Git;
required plugin distribution metadata stays tracked through an explicit exception. Shared `fleex-*`
skills come from the plugin and are not copied into the repository.

Agent-facing files are written in English. Human docs are written in English and translated to the
languages `AGENTS.md` lists (`translated to: ru`): `README.md` as `docs/ru/README.md`, a `docs/`
page at the same path inside `docs/ru/`, each file of a set with one language switcher line under
its heading. Translations may lag during development with an outdated note and are synchronized on
request, including before a PR.

## Branches and releases

`develop`, the default branch, is the working branch that all branches and PRs start from and
target, and `main` holds releases. A repository that deploys to a test server adds `staging`:
`develop` merges into it for deployment, its bugs are fixed on `develop`, and only `staging`
merges into `main`. Task branches are named `<type>/<description>`. A repository keeps its own
branch names when the user names them.

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

## VS Code

Invoke `$fleex-vscode` to prepare the VS Code workspace for a task: it picks sets from
`skills/fleex-vscode/assets/` by the task and the project files and merges their extension
recommendations and settings into the project's `.vscode/`, which stays ignored by Git. On a new
machine the whole set installs at once: `Extensions: Show Recommended Extensions`, then the Install
Workspace Recommended Extensions button. The agent may suggest other extensions for the task but
never suggests removing yours, and it installs nothing itself. Only when you ask it to sync installed
extensions with the recommendations does it install the missing ones and then, as a separate step
you confirm, uninstall the extras.

| Set | When |
| --- | --- |
| `default` | Always: editor, Git, Markdown, YAML, TOML, EditorConfig |
| `personal` | Always: theme and layout |
| `python` | Python projects |
| `cpp` | C and C++ projects |
| `infrastructure` | Docker, CI, shell scripts, remote hosts |
| `tools` | REST, draw.io, hex, CSV, XML, Inno Setup, npm |

Keybindings and settings with application or machine scope work only in the user profile; keep them
there, for example with Settings Sync.

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
