# TODO

**English** · [Русский](docs/ru/TODO.md)

States: `- [ ]` open, `- [-]` declined.
Tags: `#bug`, `#security`, `#reliability`, `#ci`, `#tests`, `#chore`.

## P0 — blocks a release

- [ ] Fix the red CI on `main`: `check.sh` requires a `.agents/skills` symlink #ci #bug
  - `.agents/` exists in every clone because of the tracked `.agents/plugins/marketplace.json`,
    while `.gitignore` excludes `/.agents/*`; the check in
    [check.sh:61-64](skills/fleex-skills/scripts/check.sh#L61-L64) and `check.ps1` fails on a
    fresh clone.
  - Decide: commit the symlink or relax the check. Release 0.3.2 is blocked by this.
- [ ] Stop the stop hook from silently dropping files with non-ASCII names #bug
  - `changed()` calls `git diff`/`ls-files` without `-z`, git quotes the name, and `is_file()` is
    false ([agentfleex.py:92-99](hooks/agentfleex.py#L92-L99)). `index.py` already uses `-z`.

## P1 — security

- [ ] Bind consent to the contents of tool configuration, not only to the set of tools #security
  - An `eslint.config.js` or mypy plugin changed by a `pull` runs without asking
    ([agentfleex.py:168-169](hooks/agentfleex.py#L168-L169)).
- [ ] Prevent the agent from recording consent without the user #security
  - The hook gives the agent a ready `consent yes` command; the guarantee rests on the agent
    obeying.
- [ ] Do not run `poetry env info` before consent #security
  - Poetry 2 can install plugins declared in `pyproject.toml`
    ([checks.py:166-176](skills/fleex-hygiene/scripts/checks.py#L166-L176)).
- [ ] Remove the data fallback to the shared `/tmp/agentfleex` #security
  - Without `CLAUDE_PLUGIN_DATA`/`PLUGIN_DATA`, another user of the machine can plant
    `consent.json` ([agentfleex.py:69-71](hooks/agentfleex.py#L69-L71)).
- [ ] Escape `%` in file names on Windows #security
  - With `shell=True`, cmd expands `%VAR%` from a file name
    ([agentfleex.py:112](hooks/agentfleex.py#L112)).
- [ ] Pin the versions of the default `uvx ruff` / `uvx mypy` #security
  - Without a version, check results drift over time.

## P2 — reliability

- [ ] Reconcile timeouts: 120 s per command against 600 s for the whole stop hook #reliability
  - With many tools the hook is killed without a clear error.
- [ ] Handle an invalid `package.json` in the stop hook #reliability #bug
  - `checks.rows` raises `SystemExit`, the hook exits with code 1, and no checks run
    ([checks.py:311](skills/fleex-hygiene/scripts/checks.py#L311)).
- [ ] Count lines in the Read hook without loading the whole file into memory #reliability
  - [agentfleex.py:263](hooks/agentfleex.py#L263).
- [ ] Protect the session state JSON from concurrent writes #reliability
  - Parallel Read hooks lose writes, and the outline is shown again.

## P3 — maintenance

- [ ] Remove the duplicated logic of `check.sh` and `check.ps1` or add an equivalence test #chore
- [ ] Decouple pushes to `main` from releases #ci
  - `version.py --check` requires a version bump even for a README fix.
- [ ] Clean up `.gitignore` #chore
  - Typo `/.agetns/`.
  - `.vscode/` is ignored while `.vscode/settings.json` is tracked.
- [ ] Add tests that would have caught the P0 tasks #tests
  - Names with spaces and Unicode in the stop hook.
  - Command escaping on Windows.
  - `check.sh` on a fresh clone.
