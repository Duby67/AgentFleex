# TODO

**English** · [Русский](docs/ru/TODO.md)

States: `- [ ]` open, `- [-]` declined.
Tags: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

## P0 — blocks a release

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

- [ ] Enable private vulnerability reporting on GitHub #security
  - [SECURITY.md](.github/SECURITY.md) sends reports to **Report a vulnerability**, but the
    repository has it disabled (`gh api repos/Duby67/AgentFleex/private-vulnerability-reporting`
    returns `"enabled":false`). Settings → Code security → Private vulnerability reporting.

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

## P3 — features

- [ ] Create the `fleex-repo` skill: audit and templates for repository service files #feature
  - Combined mode: the audit reports missing required files as errors and missing recommended
    files as suggestions; findings can go to `TODO.md` through `fleex-todo`.
  - Decide the lists. Proposal, required: `README.md`, `LICENSE`, `.gitignore`, `.gitattributes`,
    `AGENTS.md`; recommended: `.editorconfig`, `SECURITY.md`, `CONTRIBUTING.md`, `CODEOWNERS`,
    issue and PR templates, Dependabot, CI conventions (actions pinned by SHA, minimal
    `permissions`).
  - Platforms: GitHub in full; GitLab only for small projects with minimal files.
  - Rare jobs go to `references/` of this skill, loaded on demand, not to separate skills.
- [ ] Create the `fleex-release` skill from this repository's release mechanism #feature
  - Version in the manifests, pre-commit check ([.pre-commit-config.yaml](.pre-commit-config.yaml)),
    `CHANGELOG.md` with `## [x.y.z](tag link)` and a brief list, CI tags and releases only a new
    version ([ci.yml](.github/workflows/ci.yml)).
  - Decide for GitLab: release through CI or tags only.
- [ ] Add a `fleex-skills` rule: a rare job goes to `references/` of a related skill #feature
  - Keeps the always-loaded descriptions few; the current ~700 tokens of 7 descriptions are
    accepted.
- [ ] Add `fleex-hygiene` defaults for Markdown, YAML, JSON, and `.editorconfig` #feature
  - Defaults exist only for Ruff, mypy, and ShellCheck
    ([checks.py:258-289](skills/fleex-hygiene/scripts/checks.py#L258-L289)).
- [ ] Extend read savings beyond the Read tool #tokens
  - The hook matches only `Read` ([hooks.json:17](hooks/hooks.json#L17)); `cat`, `grep -r`, and
    long Bash output bypass it.
- [ ] Shorten stop hook messages #tokens
  - Each failed check returns up to 4000 characters of output
    ([agentfleex.py:50](hooks/agentfleex.py#L50)).
- [ ] Automate skill activation tests #tests
  - [fleex-skills](skills/fleex-skills/SKILL.md#L94) describes about ten manual prompts per
    skill; check whether `claude plugin eval` fits.
- [ ] Add a CI check of the always-loaded token budget #tokens
  - `AGENTS.md` plus all skill descriptions; guards growth, not the current size.
- [ ] Update the README and manifest descriptions to the new scope #docs
  - They still say the plugin keeps `AGENTS.md`, skills, and documentation short
    ([README.md:5-6](README.md#L5-L6)).

## P4 — maintenance

- [ ] Remove the duplicated logic of `check.sh` and `check.ps1` or add an equivalence test #chore
- [ ] Clean up `.gitignore` #chore
  - Typo `/.agetns/`.
- [ ] Decide how `.github/SECURITY.md` is translated #docs
  - Human docs are translated to ru, but `check.sh` and `fleex-i18n` accept translations only of
    root files and `docs/` pages; move the file to the root or extend the rule.
- [ ] Add tests that would have caught the P0 tasks #tests
  - Names with spaces and Unicode in the stop hook.
  - Command escaping on Windows.
  - `check.sh` on a fresh clone.
