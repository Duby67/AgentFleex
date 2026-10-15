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
written in English. Translations appear only when the user asks for them or `AGENTS.md` already
lists languages, and all live under `docs/<code>/`: `README.md` as `docs/ru/README.md`, a `docs/`
page at the same path inside `docs/ru/`, each file of a set with one language switcher line under
its heading. `AGENTS.md` lists the languages (`translated to: ru`); removing one deletes its files
and moves nothing else. In chat the agent replies in the language of the question.

## Hooks

The plugin ships `hooks/hooks.json`, which Claude Code and Codex both load:

- before the agent stops, the fleex-hygiene checks that take files run on the files changed against
  `HEAD`, once per state of those files, and their failures send the agent back to fix them. Linters
  run the repository's own configuration, which can execute code, so the agent first asks you
  whether to allow them in that repository; the answer is kept in the plugin's data, not in the
  repository, and a new set of tools asks again. `git diff --check` runs without asking;
- in Claude Code, the first whole read of a file over 400 lines is denied with its fleex-index
  outline, so the agent reads only the ranges it needs; repeating the read reads the whole file.

Hooks need `python3` or `python` on `PATH`. Codex runs a plugin hook only after you trust it in
`/hooks`.

## VS Code

Ask the agent to prepare the VS Code workspace for a task: the `fleex-vscode` skill picks sets from
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

## Repository layout

The repository root is the plugin root; skills live in `skills/`, hooks in `hooks/`. Manifests:
`.claude-plugin/` and `.codex-plugin/` (plugin), `.claude-plugin/marketplace.json` and
`.agents/plugins/marketplace.json` (marketplaces). To try skill changes, start Claude Code with
`claude --plugin-dir .`; in Codex, reinstall the plugin from the local marketplace. Tests for the
skill and hook scripts live in `tests/` and run with
`uv run --locked python -m unittest discover -s tests`; CI
runs them on Linux, macOS, and Windows with Python 3.9 and the latest Python, with and without
Universal Ctags. Every other check is a pre-commit hook in
[.pre-commit-config.yaml](./.pre-commit-config.yaml): Ruff, mypy, ShellCheck, file hygiene, and the
version check. Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
`uv sync --locked` to create the ignored `.venv` from `pyproject.toml` and `uv.lock`.
Use `uv add --dev` for development dependencies and `uv run --locked` for Python commands.
Install the commit hook once with `uv run --locked pre-commit install`; check all files with
`uv run --locked pre-commit run --all-files`. VS Code's Python settings set defaults to `.venv`;
if an interpreter was already selected, choose it with `Python: Select Interpreter`.

The version is owned by `project.version` in `pyproject.toml`. After changing it, run `uv lock`
and `uv run --locked python .github/scripts/release.py sync` to update both plugin manifests.
Installed plugins pick up changes only after the version is raised.
Changes are noted under `## Unreleased` in [CHANGELOG.md](./CHANGELOG.md); a release renames
that section to the version. Work goes to `develop`, and every merge into `main` is a release.
[release.py](./.github/scripts/release.py) checks that both manifests match the TOML x.y.z version, that
`CHANGELOG.md` has its section, and that translations have the same headings. A push to `develop`
runs the tests and pre-commit; a pull request into `main` shows those results for its head commit
and adds the release check: an empty `## Unreleased`, notes in every changelog, and a version above
the latest tag. Require these checks for `main` in the branch protection settings, so a failing
`develop` cannot be merged. A push to `main` repeats the release check, tags the version, and
publishes it as the latest release with the notes of its section, each translation's section
collapsed under its language name. Security reports: [SECURITY.md](./.github/SECURITY.md). Licensed
under [MIT](./LICENSE).

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
owns human documentation; [fleex-i18n](./skills/fleex-i18n/SKILL.md) owns its translations;
[fleex-index](./skills/fleex-index/SKILL.md) is a dependency-free navigation script (map, outline,
show, find, refs) so agents read only the lines they need;
[fleex-hygiene](./skills/fleex-hygiene/SKILL.md) finds and runs the repository's configured linters,
formatters, and type checkers so every change keeps one style.
[fleex-todo](./skills/fleex-todo/SKILL.md) owns the `TODO.md` backlog of verified findings and
planned work. Existing configuration always wins;
where a repository has none, the plugin's defaults in `skills/fleex-hygiene/assets/` apply. This
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
