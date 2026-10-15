# Contributing

## Issues

Report bugs and propose features with the issue forms. Report vulnerabilities privately as
described in `docs/SECURITY.md`.

## Setup

<!-- The commands that install the environment and the commit hook. -->

## Checks

<!-- The test command and `pre-commit run --all-files`. -->

## Branches

- `develop` is the working branch: start every branch from it and target every pull request at it.
  It holds only finished changes, so it can be released at any time.
- `main`, the default branch, holds releases: only `develop` merges into it.
- Task branches are named `<type>/<description>`: a lowercase kebab-case description of two to
  five words, optionally starting with an issue number. Types: `feat/` new behavior, `fix/` bug
  fix, `docs/` documentation only, `refactor/` no behavior change, `test/` tests only, `ci/` CI and
  release workflows, `chore/` maintenance, `claude/` and `codex/` branches created by agents.

## Pull requests

- One change per pull request into `develop`; the checks pass after the last commit.
- Note user-visible changes under `## Unreleased` in `docs/CHANGELOG.md`.

## Versions and releases

Versions follow Semantic Versioning. Every merge into `main` is a release: raise the version on
`develop`, rename `## Unreleased` to the version, open a pull request from `develop` into `main`,
and merge it with a merge commit; CI tags and publishes the release.

## License

Contributions are licensed under the project's license.
