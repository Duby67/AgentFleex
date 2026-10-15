# Changelog

**English** · [Русский](ru/CHANGELOG.md)

## Unreleased

- Moved `CHANGELOG.md` and `TODO.md` to `docs/`; the release check reads `docs/CHANGELOG.md`, and
  `fleex-docs` creates a new backlog as `docs/TODO.md`.
- Added `docs/CONTRIBUTING.md` with setup, checks, branch naming (`<type>/<description>`), pull
  requests, Semantic Versioning, and the release steps; the README links to it instead of
  describing development.
- Added issue forms for bugs and features, a pull request template, and a contact link for private
  vulnerability reports; blank issues are disabled.
- CI fails a pull request into `main` from any branch other than `develop`.
- The `AGENTS.md` rule catalog names task branches `<type>/<kebab-description>`.
- `fleex-vscode` runs only when invoked explicitly, so its description no longer loads into every
  request in Claude Code or Codex.
- The `fleex-todo` skill became a `fleex-docs` reference, read only when `TODO.md` is edited.
- Translations moved from the `fleex-i18n` skill into `fleex-docs` as an on-demand reference;
  translation passes still run only on request.
- Removed automatic stop-time checks and consent prompts; hygiene and translations now require
  explicit invocation, with full checks before PRs or merges and translation lag allowed in development.
- Read hooks count lines in bounded buffers and use atomic per-file session markers with private
  plugin data; concurrent reads no longer lose state or repeatedly deny the same file.
- Rare subtasks belong in related skills' references; standalone skills retain distinct triggers.
- Made `pyproject.toml` the version source; `release.py sync` updates both plugin manifests,
  and pre-commit and CI reject version mismatches.
- Added a uv-managed development environment with a lockfile, `.venv`, and matching CI commands;
  Python repositories default to uv, and VS Code's Python settings point to `.venv`.

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
