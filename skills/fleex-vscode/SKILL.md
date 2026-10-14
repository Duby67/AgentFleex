---
name: fleex-vscode
description: Prepare a project's VS Code workspace for a task by writing extension recommendations and settings from AgentFleex sets into its ignored .vscode/. Use when the user asks to set up, prepare, or adjust the VS Code workspace, its extensions, or its editor settings. Do not use for VS Code user profiles, keybindings, or launch and task configurations.
---

# VS Code workspace

`assets/<set>/` (relative to this skill's directory) holds `extensions.json` (recommendations) and
`settings.json` for one set:

| Set | When |
| --- | --- |
| `default` | Always: editor, Git, Markdown, YAML, TOML, EditorConfig |
| `personal` | Always: theme, layout, AI assistants |
| `python` | `pyproject.toml`, `setup.py`, or Python sources |
| `cpp` | `CMakeLists.txt` or C/C++ sources |
| `infrastructure` | Dockerfiles, compose files, CI workflows, shell scripts, remote hosts |
| `tools` | REST, draw.io, hex, CSV, XML, or Inno Setup files, or when the user asks |

Choose sets from the task and the files present, then merge them into `.vscode/extensions.json`
and `.vscode/settings.json` at the repository root: union of `recommendations` in set order, and
settings where a later set wins. Keys already in the project's files win over sets; report each
conflict instead of overwriting it. Read only the chosen sets.

`.vscode/` stays out of Git: add `/.vscode/` to `.gitignore` if it is missing. If Git already
tracks files under `.vscode/`, stop and report them instead of untracking or editing them.

VS Code applies workspace settings on save and offers to install the recommendations; settings with
application or machine scope and keybindings take effect only in the user profile, so leave those
to the user.
