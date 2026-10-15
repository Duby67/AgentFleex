# AgentFleex

**English** · [Русский](docs/ru/README.md)

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
| `AGENTS.md` | The single rules file and the only entry point; Codex reads it natively |
| `.claude/CLAUDE.md` | Claude Code only: one line, `@../AGENTS.md`, imports the same file |
| Skills source | The repository's top-level `skills/`, when project skills exist |
| `.agents/skills`, `.claude/skills` | Relative symlinks to the source, only for agents in use: Codex reads `.agents/skills`, Claude Code `.claude/skills` |

An agent's directory (`.claude/`, `.cursor/`) is created only when the repository uses that agent
and is ignored by Git. Local imports and symlinks stay on disk; required plugin distribution
metadata remains tracked through an explicit exception.

Shared `fleex-*` skills come from the plugin and are not copied into the repository. Both clients
find skills by their `description` field, so `AGENTS.md` needs no routing table.

Agent-facing files (`AGENTS.md`, skills, agent docs) are written in English. Human docs are
written in English. Translation passes run on request, including before a PR; translations may
lag during development, with an outdated note linking the English source. Languages are listed in
`AGENTS.md`, and all translations live under `docs/<code>/`: `README.md` as `docs/ru/README.md`, a `docs/`
page at the same path inside `docs/ru/`, each file of a set with one language switcher line under
its heading. `AGENTS.md` lists the languages (`translated to: ru`); removing one deletes its files
and moves nothing else. In chat the agent replies in the language of the question.

## Hooks

The plugin ships only a `PreToolUse` hook matching Claude Code's `Read` tool. The first whole read
of a file over 400 lines is denied with its fleex-index outline; repeating the read allows the
whole file. Ranged reads and short or binary files pass through. Line counting uses bounded
buffers, and atomic markers prevent repeated denials when reads run concurrently.

Hooks need `python3` or `python` on `PATH` and `CLAUDE_PLUGIN_DATA` or `PLUGIN_DATA` pointing to
a private plugin data directory. There is no shared temporary-directory fallback. Codex must trust
plugin hooks in `/hooks`, but this matcher does not intercept shell commands or other read tools.

`$fleex-hygiene` and `$fleex-vscode` run only when invoked explicitly, so their descriptions
cost no context; translation passes run only on request, for example when preparing a
PR or merge. Neither checks nor translations run after every edit or response. Existing pre-commit
and CI checks remain the validation checkpoints.

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

## Contributing

Development setup, checks, branches, pull requests, and releases:
[CONTRIBUTING.md](docs/CONTRIBUTING.md). Security reports: [SECURITY.md](./.github/SECURITY.md).
Licensed under [MIT](./LICENSE).

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
`.claude/CLAUDE.md`, and the single catalog of shared rules; [fleex-skills](./skills/fleex-skills/SKILL.md)
owns skills, their wiring, and links to best practices; [fleex-docs](./skills/fleex-docs/SKILL.md)
owns human documentation and, in its references, [translations](./skills/fleex-docs/references/i18n.md)
and the [`TODO.md` backlog](./skills/fleex-docs/references/todo.md);
[fleex-index](./skills/fleex-index/SKILL.md) is a dependency-free navigation script (map, outline,
show, find, refs) so agents read only the lines they need;
[fleex-hygiene](./skills/fleex-hygiene/SKILL.md) finds and runs the repository's configured linters,
formatters, and type checkers on request or for a requested PR or merge check. Existing
configuration always wins; where a repository has none, the plugin's defaults in `skills/fleex-hygiene/assets/` apply. This
repository uses them too: `ruff.toml` extends the default Ruff config, and CI passes the default
mypy config. Rules once written into a repository's `AGENTS.md` belong to its owner and are not
synced with the catalog.

Every `AGENTS.md` gets one branch model: `develop` is the working branch that all branches, forks,
and PRs start from and target; `staging` receives `develop` for deployment to the test server, and
its bugs are fixed on `develop`; `main`, the default branch, takes only tested `staging` and holds
releases. A repository keeps its own branch names when the user names them.

## References

- [AGENTS.md](https://agents.md), [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md),
  [Claude Code: memory](https://docs.claude.com/en/docs/claude-code/memory)
- [Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices),
  [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- Skills: [specification](https://agentskills.io/specification),
  [best practices](https://agentskills.io/skill-creation/best-practices),
  [Anthropic examples](https://github.com/anthropics/skills), [OpenAI examples](https://github.com/openai/skills)
