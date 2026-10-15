# Changelog

**English** · [Русский](ru/CHANGELOG.md)

## Unreleased

## [0.4.0](https://github.com/Duby67/AgentFleex/releases/tag/0.4.0)

- Added the `fleex-repo` skill, invoked explicitly: it audits and sets up a GitHub repository's
  service files and settings (LICENSE, `.gitignore`, `.gitattributes`, SECURITY and CONTRIBUTING
  skeletons, issue forms and a PR template, Dependabot, CI, private vulnerability reporting) and its
  releases, from templates taken from this repository.
- `fleex-repo` ships `release.py` for any repository: the version comes from `pyproject.toml`,
  `package.json`, or `VERSION`, `--manifest` files stay in sync, and CI rejects a pull request into
  `main` from any branch but the release source, then tags each merge into `main` and publishes it
  with notes from `docs/CHANGELOG.md`.
- Fewer skill descriptions load into every request: translations and the `TODO.md` backlog became
  `fleex-docs` references, replacing `fleex-i18n` and `fleex-todo`, and `fleex-vscode` runs only
  when invoked explicitly. Tests cap the size of `AGENTS.md` and of the automatic descriptions.
- `fleex-hygiene` loads automatically but runs only on request or before a PR or merge; automatic
  stop-time checks and consent prompts are gone. Its setup guide is a reference with templates for
  `.editorconfig` and a base pre-commit configuration.
- markdownlint and yamllint joined Ruff, mypy, and ShellCheck as hygiene defaults, and default tools
  run through `uvx` or `npx` at pinned versions, so results no longer drift with new releases.
- `fleex-hygiene` no longer runs Poetry, which can install plugins the repository declares, to find
  the project environment, and fails with an actionable error instead of printing a command whose
  path contains `%`, which cmd expands on Windows.
- Python repositories default to uv with a committed `uv.lock` and an ignored `.venv`; VS Code's
  Python settings point to `.venv`.
- The branch model adds `staging` only for repositories that deploy to a test server, and task
  branches are named `<type>/<kebab-description>`.
- Human docs other than the README live in `docs/` (`CHANGELOG.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, `TODO.md`), each translated to Russian; new backlogs are created as
  `docs/TODO.md`.
- The Read hook counts lines in bounded buffers and keeps atomic per-file markers in private plugin
  data, so concurrent reads no longer lose state or deny the same file twice.

## [0.3.3](https://github.com/Duby67/AgentFleex/releases/tag/0.3.3)

- Fixed release notes failing on Cyrillic text on Windows by writing UTF-8 output.
- Release notes now describe solved problems and resulting behavior without task-list bookkeeping.
- Added the `fleex-vscode` skill: VS Code extension recommendations and settings by set, merged
  into the project's ignored `.vscode/`; it may suggest other extensions, never suggests removing
  installed ones, and on request syncs installed extensions with the sets, uninstalling extras as a
  separate confirmed step.
- Stopped tracking `.vscode/settings.json`; `.vscode/` is ignored.
- Added a branch model to the `AGENTS.md` rule catalog: `develop` for work, `staging` for
  testing, `main` for releases.
- Development moved to `develop`: a push to it runs the tests and pre-commit, a pull request into
  `main` adds the release check, and a push to `main` releases.
- Ruff, mypy, ShellCheck, and file checks run as pre-commit hooks; `fleex-hygiene` makes pre-commit
  the hygiene runner of every repository and checks a tool it lists only through it.
- Every merge into `main` is a release: CI fails a version that is not above the latest tag, and
  `.github/scripts/release.py` holds the version and changelog checks for CI and pre-commit.

## [0.3.2](https://github.com/Duby67/AgentFleex/releases/tag/0.3.2)

- Added the `fleex-todo` skill for the `TODO.md` backlog.
- Added `CHANGELOG.md`, `.github/SECURITY.md`, and `.gitattributes`.
- Replaced `VERSION` and `version.py` with a pre-commit check of the manifest versions.
- CI releases a manifest version that has no GitHub release yet, with notes from `CHANGELOG.md`;
  changes wait under `## Unreleased` until the release, and translations are collapsed under their
  language names.
- Fixed the skill check failing on a clean clone because of committed plugin metadata in
  `.agents/`, and on macOS, where bash 3.2 matched `./skills` as an agent skills path.

## [0.3.1](https://github.com/Duby67/AgentFleex/releases/tag/0.3.1)

- Added root `VERSION` and a script that synchronized the manifest versions.
- Moved project skills to the top-level `skills/`, with symlinks for agents.

## [0.3.0](https://github.com/Duby67/AgentFleex/releases/tag/0.3.0)

- Added the `fleex-i18n` skill.
- Added hooks: style checks before the agent stops and outlines for long reads.
- Added CI on Linux, macOS, and Windows, and Dependabot.

## [0.2.0](https://github.com/Duby67/AgentFleex/releases/tag/0.2.0)

- Added the `fleex-index` and `fleex-hygiene` skills.
- Renamed `fleex-agents-md` to `fleex-agents`.

## [0.1.0](https://github.com/Duby67/AgentFleex/releases/tag/0.1.0)

- Created the plugin with the `fleex-agents-md`, `fleex-docs`, and `fleex-skills` skills.
