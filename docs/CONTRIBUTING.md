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

- Start each change on a task branch from `develop`, the default branch, and target its PR at
  `develop`.
- Release PRs go from `develop` to `main`, where a merge commit triggers publication.
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

## Releases

See [Releasing AgentFleex](RELEASING.md).

## License

Contributions are licensed under the [MIT License](../LICENSE) of the project.
