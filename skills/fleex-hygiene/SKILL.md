---
name: fleex-hygiene
description: Diagnose and fix lint, formatting, and type-check failures using the project's configured checks. Use for reported diagnostics, verification before a commit or PR, or explicit requests to set up tooling.
---

# Hygiene

Use the repository's commands and CI configuration. Run the fastest check that reproduces a
reported failure, fix its cause, and rerun that check. Before a commit or PR, and after substantial
changes, run the project's required checks for that milestone. Reuse results for unchanged inputs.

- Prefer configured pre-commit hooks or task commands when they already run the check.
- Use formatters and safe autofixes. Keep existing rules and report unrelated failures.
- If the commands are unclear, run `scripts/checks.py` with Python 3.9+ from the repository. It
  lists configured checks and CI commands. Replace `{files}` with relevant changed files.
  Report missing tools or use the project's documented setup when authorized.
- For requested tooling setup, follow [the setup guide](references/setup.md).
