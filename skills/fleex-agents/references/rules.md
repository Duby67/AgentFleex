# Rule catalog

Shared rules for `AGENTS.md`, grouped by the section they go in. Use a rule only when it holds for
the repository; replace `<...>` with verified commands and paths.

## Rules

Hard rules; stop and report instead of working around them.

- No silent fallback: fail with an actionable error.
- Secrets come from the environment; never commit or log them.
- Start another agent only with the user's permission.
- When docs, config, code, and tests disagree, report the contradiction instead of choosing.

## Work

- Reuse existing code and make the smallest complete change. Read only the relevant sections.
- Run development commands and tests through the project's configured environment and tools.
  Specify `<project command>` when it helps agents use that environment.
- Use targeted checks or a quick functional check for routine changes. Run full checks on
  request, before a commit or PR, or after substantial feature changes. Report results for the
  state actually checked.
- Do not create plan, summary, or notes files unless asked.
- Add files to existing or tool-specific directories. Use the root only when a tool requires it.

## Language

Write agent-facing files and human documentation in English.

## Report

Briefly report completed work, outcomes of checks actually run, and concrete risks.
Omit actions you did not take.
