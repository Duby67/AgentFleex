# Security policy

## Supported versions

Only the latest release gets security fixes; update the plugin before reporting.

## Reporting a vulnerability

Report privately through GitHub: open the repository's **Security** tab and choose **Report a
vulnerability**. Do not open a public issue, pull request, or discussion for a vulnerability.

Include the plugin version, the client (Claude Code or Codex) and operating system, the steps or a
minimal repository that reproduces the problem, and what an attacker gains.

## Scope

AgentFleex hooks run inside your agent session and start other programs:

- before the agent stops, the repository's own linters and type checkers on changed files, once
  the user agreed for that repository and set of tools;
- `git` and the plugin's Python scripts at any time.

In scope, for example: a hook or script running repository code or a downloaded tool without that
agreement, consent recorded without the user, command injection through file names or
configuration, and plugin data that another local user can read or change. Out of scope: what a
linter does once the user allowed it, and the behavior of the clients themselves.
