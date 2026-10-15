---
name: fleex-vscode
description: Prepare a project's VS Code workspace for a task by writing extension recommendations and settings from AgentFleex sets into its ignored .vscode/, and, only on explicit request, sync installed VS Code extensions with those sets. Use when the user asks to set up, prepare, or adjust the VS Code workspace, its extensions, or its editor settings, or to sync installed extensions with the recommendations. Do not use for VS Code user settings, profiles, keybindings, or launch and task configurations.
---

# VS Code workspace

`assets/<set>/` (relative to this skill's directory) holds `extensions.json` (recommendations) and
`settings.json` for one set. Sets list each extension by its own ID, never an extension pack:

| Set | When |
| --- | --- |
| `default` | Always: editor, Git, Markdown, YAML, TOML, EditorConfig |
| `personal` | Always: theme and layout |
| `python` | `pyproject.toml`, `setup.py`, or Python sources |
| `cpp` | `CMakeLists.txt` or C/C++ sources |
| `infrastructure` | Dockerfiles, compose files, CI workflows, shell scripts, WSL, remote hosts |
| `tools` | REST, draw.io, hex, CSV, XML, Inno Setup, or npm `package.json` files, or on request |

Choose sets from the task and the files present, then merge them into `.vscode/extensions.json`
and `.vscode/settings.json` at the repository root: union of `recommendations` in set order, and
settings where a later set wins. Keys already in the project's files win over sets; report each
conflict instead of overwriting it. Read only the chosen sets.

`.vscode/` stays out of Git: add `/.vscode/` to `.gitignore` if it is missing. If Git already
tracks files under `.vscode/`, stop and report them instead of untracking or editing them.

Beyond the sets, you may suggest extensions the task or files call for; name them apart from the
set recommendations and add them only when the user agrees. The sets are a starting point, not a
standard: never suggest removing an installed extension the sets lack, and outside a requested
sync never install, enable, disable, or uninstall extensions. Tell the user to install the
recommendations with `Extensions: Show Recommended Extensions` and its Install Workspace
Recommended Extensions button. Keybindings, profiles, and settings with application or machine
scope live in the user profile and stay with the user.

## Sync on request

Only when the user explicitly asks to sync installed extensions with the recommendations, make
each extension host (local, and the WSL, SSH, or container server when one is used) hold exactly
the chosen sets, plus the extensions that connect the local client to those servers. Use the
host's CLI (`code`; on a server, `~/.vscode-server/bin/*/bin/code-server`) with
`--list-extensions`, `--install-extension`, and `--uninstall-extension`; never delete extension
folders directly. Install missing extensions first. Removal is a separate step: show the extras per
host and uninstall only the ones the user confirms.

- Uninstalling an extension pack also uninstalls its members: list again after removal and
  reinstall chosen extensions that disappeared.
- Settings Sync can restore removed extensions on another machine or the next start; say so when
  it is on.
- Leftover data of removed extensions (`globalStorage`, `workspaceStorage`, cached VSIX files) is
  the user's to clean up; list it only when asked.

Finish by listing each host's extensions again and reporting any difference from the target.
