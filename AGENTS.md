# Agents

Repository router for coding agents. Human overview: `README.md`. Skills live in `Skills/`
(`.agents/skills` and `.claude/skills` are symlinks to it); use a skill only when it adds
task-specific guidance.

## Project

AgentFleex is a language-neutral template for repositories developed with coding agents: agent
rules, shared skills, Git process, and the checks that keep them consistent. A project created from
it replaces this section with what the project is and is not, and adds its domain invariants,
sources of truth, and project skills.

## Invariants

These are hard rules. Stop and report instead of working around them.

- **Protected branches.** `integration` is the cumulative PR target; `dev` and `production` are
  promotion and deployment branches. Never edit or commit while checked out on any of them. Work on
  a dedicated branch created from current `origin/integration`. The developer owns commit, push, PR,
  and merge; agents do not perform them. Full policy: `Docs/GIT_WORKFLOW.md`.
- **No silent fallback** in data, money, identity, configuration, or deploy paths: fail with an
  actionable error instead of substituting a default.
- **Secrets and privacy.** Secrets, tokens, and connection strings come from the environment, never
  from committed files. Never commit credentials, and keep secrets and personal data out of logs,
  reports, and session files.
- **No delegation.** Only the operator starts agents; agents never invoke other agents.
- **Honest evidence.** Never describe an unrun, skipped, or platform-skipped check as passed.
  Completion requires relevant checks run after the last change; earlier results are not fresh evidence.

## Sources of truth

| Area | Canonical owner |
| --- | --- |
| Branches, promotion, version | `Docs/GIT_WORKFLOW.md` |
| Test philosophy and commands | `Tests/README.md` |
| Documentation index | `Docs/README.md` |

`TODO.md` is backlog only. When docs, config, code, and tests disagree, report the contradiction
instead of choosing silently. Link to owners instead of copying volatile values.

## Task routing

Read only what the task needs; skills are guidance, not mandatory stages.

| Task | Consider first |
| --- | --- |
| Human-facing Markdown | `Skills/kit-docs/SKILL.md` |
| `AGENTS.md`, Git policy, skill routing checks | `Skills/kit-agent-rules/SKILL.md` |
| Creating or reviewing skills | `Skills/kit-skill-authoring/SKILL.md` |

## Change discipline

Trace the real flow before editing, then make the smallest correct change in the shared code path.
Prefer, in order: no change, existing code, the standard library, an installed dependency, new code.
Add no abstraction, option, config key, or dependency the task did not need; prefer deleting to
adding; stay in scope. Tests supporting a change belong to it. These rules never shorten validation
at trust boundaries, data-loss handling, security, privacy, or the invariants.

Keep output lean: focused `rg` and bounded `sed` reads, `git diff --stat` before diffs, quiet test
runs; save long output to a file and read an excerpt, keeping the exit status.

## Collaboration

Work directly from the request; plan only when risk warrants it. For multi-session work keep
`.agents/handoff.md` as a current snapshot of findings, decisions, and evidence; `.agents/tasks.md`
holds the operator's task list (one checkbox with a done criterion per task; mark results, add no
tasks). Both are local, git-ignored, in the operator's language, and never contain secrets or
personal data. Concurrent implementation needs separate worktrees. Move durable lessons to their
canonical docs or skills.

## Handoff

One line per point; no task retelling, file tours, or defense of the approach. Report results and
checks actually performed; never list actions or checks not performed, repeat visible repository
state, or announce journal updates. Omit empty categories. Report failures and blockers directly and
never imply completion when work is blocked.

- Result: what changed.
- Checks: the commands actually run and their outcome.
- Risks: concrete data, security, privacy, configuration, or deploy risks that affect the result.

Change the project version only when the developer explicitly asks.

## Language

`AGENTS.md` and `Skills/**` are English (except user-facing `agents/openai.yaml` fields of project
skills, per `$kit-skill-authoring`); `.agents/` session files follow the operator; human
documentation is Russian.
