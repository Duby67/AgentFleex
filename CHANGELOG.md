# Changelog

**English** · [Русский](docs/ru/CHANGELOG.md)

## Unreleased

- Added the `fleex-vscode` skill: VS Code extension recommendations and settings by set, merged
  into the project's ignored `.vscode/`.
- Stopped tracking `.vscode/settings.json`; `.vscode/` is ignored.

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
