---
name: fleex-vscode
description: Set up a VS Code profile from AgentFleex extension packs and settings, or add packs to a profile. Runs only when the user invokes it.
disable-model-invocation: true
---

# VS Code

Run `scripts/vscode.py` (relative to this skill's directory) with Python 3.9+; it does the whole
job, so do not read the packs or settings yourself.

- `list`: packs with their purpose, and the packs of each profile.
- `apply <profile> [--add PACK...] [--open DIR]`: create the profile if missing, install its packs
  plus the added ones, merge their settings into the profile's `settings.json`, and optionally
  open a folder with the profile. `Default` is VS Code's own profile.

Packs are downloaded from the GitHub release of the plugin version; `--vsix DIR` uses local
`fleex-pack-*.vsix` files instead. Under WSL the script configures the Windows VS Code; afterwards,
extensions that run in WSL are installed there with the command `Install Local Extensions in 'WSL'`.

Report a failure with the script's message; never edit VS Code settings or profiles by hand
instead.
