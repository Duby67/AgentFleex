# Contributing

## Issues

Report bugs and propose features with the issue forms. Report vulnerabilities privately as
described in [SECURITY.md](SECURITY.md), never in a public issue.

## Setup

The repository root is the plugin root; skills live in `skills/`, hooks in `hooks/`, tests in
`tests/`. Manifests: `.claude-plugin/` and `.codex-plugin/` (plugin),
`.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` (marketplaces).

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run `uv sync --locked`
to create the ignored `.venv` from `pyproject.toml` and `uv.lock`, and install the commit hook once
with `uv run --locked pre-commit install`. Use `uv add --dev` for development dependencies and
`uv run --locked` for Python commands.

To try skill changes, start Claude Code with `claude --plugin-dir .`; in Codex, reinstall the
plugin from the local marketplace.

## Checks

- Tests: `uv run --locked python -m unittest discover -s tests`. CI runs them on Linux, macOS, and
  Windows with Python 3.9 and the latest Python, with and without Universal Ctags.
- Everything else: `uv run --locked pre-commit run --all-files`, the hooks in
  [.pre-commit-config.yaml](../.pre-commit-config.yaml): Ruff, mypy, ShellCheck, markdownlint,
  yamllint, file hygiene, and the version check.

## Branches

- `develop`, the default branch, is the working branch: start every branch from it and target every
  pull request at it. It holds only finished changes, so it can be released at any time.
- `main` holds releases: only `develop` merges into it.
- Task branches are named `<type>/<description>`: a lowercase kebab-case description of two to
  five words, optionally starting with an issue number (`fix/42-hook-unicode-paths`). Types:

  | Type | Purpose |
  | --- | --- |
  | `feat/` | New behavior |
  | `fix/` | Bug fix |
  | `docs/` | Documentation only |
  | `refactor/` | Code change without behavior change |
  | `test/` | Tests only |
  | `ci/` | CI and release workflows |
  | `chore/` | Dependencies, tooling, and other maintenance |
  | `claude/`, `codex/` | Branches created by Claude Code or Codex in the cloud |
  | `dependabot/` | Dependency updates created by Dependabot |

## Pull requests

- One change per pull request into `develop`, with a title stating the change; it is merged with
  **Squash and merge**, so the title becomes the commit on `develop`.
- The checks pass after the last commit.
- Note user-visible changes under `## Unreleased` in [CHANGELOG.md](CHANGELOG.md) as the solved
  problem and resulting behavior.
- Write documentation in English.

## Versions and releases

Versions follow [Semantic Versioning](https://semver.org/). While the version is `0.x`, the minor
number marks changed or removed behavior of skills and hooks, and the patch number marks fixes and
additions. Installed plugins update only when the version is raised. `develop` has no version of
its own; it carries the last released one until a release raises it.

Every merge into `main` is a release, made by the maintainer:

1. On `develop`, raise `project.version` in `pyproject.toml` above the latest tag, then run
   `uv lock` and the sync command to update both plugin manifests:

   ```bash
   uv run --locked python skills/fleex-repo/scripts/release.py \
     --manifest .claude-plugin/plugin.json --manifest .codex-plugin/plugin.json sync
   ```

2. Rename `## Unreleased` to `## [x.y.z](https://github.com/Duby67/AgentFleex/releases/tag/x.y.z)`
   in the changelog and leave an empty `## Unreleased` above it.
3. Run the local checks and push `develop`.
4. Open a pull request from `develop` into `main`. The release check verifies the source branch,
   manifest versions, an empty `## Unreleased`, notes for the new version, and a version above the
   latest tag. [Release script](../skills/fleex-repo/scripts/release.py)
5. Merge with **Create a merge commit**. Squash and rebase merges rewrite the commits, so `main` and
   `develop` diverge.
6. The push to `main` repeats the release check, tags the version, and publishes it as the latest
   GitHub release with the notes from that section.

A bug in a release is fixed on `develop` and shipped with the next patch version.

## License

Contributions are licensed under the [MIT License](../LICENSE) of the project.
