# AgentFleex

Agent plugin whose skills keep AGENTS.md, repository skills, and docs
minimal. The repository root is the plugin root, and skills live in `skills/`.

## Rules

Hard rules; stop and report instead of working around them.

- No silent fallback: fail with an actionable error.
- Secrets come from the environment; never commit or log them.
- Start another agent only with the user's permission.
- When docs, config, code, and tests disagree, report the contradiction instead of choosing.

## Work

Reuse existing code and make the smallest complete change. Read only the relevant sections.

- Follow the project's [branch workflow](docs/CONTRIBUTING.md#branches).
- Keep agent rules in `AGENTS.md` and reference it from other agent instruction files.
- Keep skills in `skills/` and link agent-specific skill paths with relative symlinks. Ignore local
  agent directories except for `.agents/plugins/marketplace.json`.
- Add files to existing or tool-specific directories. Use the root only when a tool requires it.
- Run Python commands, including tests, with `uv run --locked`. See
  [Setup](docs/CONTRIBUTING.md#setup) for environment and dependency commands.
- Run targeted checks or a quick functional check for routine changes. Run the full
  [checks](docs/CONTRIBUTING.md#checks) on request, before a PR, or after substantial feature
  changes. Report results for the state actually checked.
- Record user-visible changes under `## Unreleased` in [the changelog](docs/CHANGELOG.md).
- Read [the release instructions](docs/RELEASING.md) when preparing a release or a version bump.

## Language

Write documentation in English.

## Report

Briefly report completed work, outcomes of checks actually run, and concrete risks.
Omit actions you did not take.
