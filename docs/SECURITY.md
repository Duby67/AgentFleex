# Security policy

**English** · [Русский](ru/SECURITY.md)

## Supported versions

Only the latest release gets security fixes; update the plugin before reporting.

## Reporting a vulnerability

Report privately through GitHub: open the repository's **Security** tab and choose **Report a
vulnerability**. Do not open a public issue, pull request, or discussion for a vulnerability.

Include the plugin version, the client (Claude Code or Codex) and operating system, the steps or a
minimal repository that reproduces the problem, and what an attacker gains.

## Scope

AgentFleex starts other programs from inside your agent session:

- the Read hook runs the plugin's Python index script, which calls `git` and, when installed,
  Universal Ctags;
- skill scripts call `git` and print check commands without running them; the agent runs the
  repository's linters and type checkers only when a task or the user asks for them.

In scope, for example: a hook or script running repository code or a downloaded tool on its own,
command injection through file names or configuration, and plugin data that another local user can
read or change. Out of scope: what a linter does once it runs, and the behavior of the clients
themselves.
