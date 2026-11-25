# Rule catalog

Use these rules when writing or reviewing `AGENTS.md`. Verify project commands and paths before
adding them. Once adopted, a rule belongs to the repository owner. Catalog changes never remove
or alter an existing rule without the owner's direction.

## Universal

- Never commit or log secrets.
- Report contradictions between docs, configuration, code, and tests that affect the requested
  work. Ask which contract to follow when the contradiction blocks the work.

## Conditional

Add a rule only when the condition describes the repository or the owner's preference.

| When it helps | Rule |
| --- | --- |
| A fallback would mask a failure or change a project contract | Fail with an actionable error when the required operation cannot complete. |
| The owner limits delegation | Start another agent only with the user's permission. |
| Running outside the configured environment gives different results | Run development commands and tests through the project's configured environment. Give the verified command when useful. |
| Full checks are costly and the project defines verification milestones | Run targeted checks for routine changes. List the milestones that require full checks and report results for the state actually checked. |
| The project deliberately limits root files | Use existing or tool-specific directories for new files. Use the root where a tool requires it. |
| The owner wants terse handoffs | Briefly report completed work, outcomes of checks actually run, and concrete risks. Omit actions you did not take. |
