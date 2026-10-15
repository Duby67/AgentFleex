# TODO

**English** · [Русский](ru/TODO.md)

States: `- [ ]` open, `- [-]` declined.
Tags: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

## P1 — security

- [ ] Avoid executing Poetry while discovering checks #security
  - Poetry 2 can install plugins declared in `pyproject.toml`
    ([checks.py:166-176](../skills/fleex-hygiene/scripts/checks.py#L166-L176)).
- [ ] Escape `%` in generated check commands on Windows #security
  - `shell_path()` leaves `%VAR%` unescaped; cmd expands it if a generated command is executed
    ([checks.py:292-296](../skills/fleex-hygiene/scripts/checks.py#L292-L296)).
- [ ] Pin the versions of the default `uvx ruff` / `uvx mypy` #security
  - Without a version, check results drift over time.

- [ ] Enable private vulnerability reporting on GitHub #security
  - [SECURITY.md](../.github/SECURITY.md) sends reports to **Report a vulnerability**, but the
    repository has it disabled (`gh api repos/Duby67/AgentFleex/private-vulnerability-reporting`
    returns `"enabled":false`). Settings → Code security → Private vulnerability reporting.

## P3 — features

- [ ] Create the `fleex-repo` skill: audit and templates for repository service files #feature
  - Combined mode: the audit reports missing required files as errors and missing recommended
    files as suggestions; findings can go to `TODO.md`.
  - Decide the lists. Proposal, required: `README.md`, `LICENSE`, `.gitignore`, `.gitattributes`,
    `AGENTS.md`; recommended: `.editorconfig`, `SECURITY.md`, `CONTRIBUTING.md`, issue and PR
    templates, Dependabot, CI conventions (actions pinned by SHA, minimal `permissions`).
  - Platforms: GitHub in full; GitLab only for small projects with minimal files.
  - Rare jobs go to `references/` of this skill, loaded on demand, not to separate skills.
- [ ] Create the `fleex-release` skill from this repository's release mechanism #feature
  - Version in the manifests, pre-commit check
    ([.pre-commit-config.yaml](../.pre-commit-config.yaml)), `CHANGELOG.md` with
    `## [x.y.z](tag link)` and a brief list, CI tags and releases only a new version ([ci.yml](../.github/workflows/ci.yml)).
  - Decide for GitLab: release through CI or tags only.
- [ ] Add `fleex-hygiene` defaults for Markdown, YAML, JSON, and `.editorconfig` #feature
  - Defaults exist only for Ruff, mypy, and ShellCheck
    ([checks.py:258-289](../skills/fleex-hygiene/scripts/checks.py#L258-L289)).
- [ ] Extend read savings beyond the Read tool #tokens
  - The hook matches only `Read` ([hooks.json:6](../hooks/hooks.json#L6)); `cat`, `grep -r`, and
    long Bash output bypass it.
- [ ] Automate skill activation tests #tests
  - [fleex-skills](../skills/fleex-skills/SKILL.md#L98) describes about ten manual prompts per
    skill; check whether `claude plugin eval` fits.
- [ ] Add a CI check of the always-loaded token budget #tokens
  - `AGENTS.md` plus all skill descriptions; guards growth, not the current size.
- [ ] Update the README and manifest descriptions to the new scope #docs
  - They still say the plugin keeps `AGENTS.md`, skills, and documentation short
    ([README.md:5-6](../README.md#L5-L6)).

## P4 — maintenance

- [ ] Remove the duplicated logic of `check.sh` and `check.ps1` or add an equivalence test #chore
- [ ] Clean up `.gitignore` #chore
  - Typo `/.agetns/`.
- [ ] Decide how `.github/SECURITY.md` is translated #docs
  - Human docs are translated to ru, but `check.sh` and `fleex-docs` accept translations only of
    root files and `docs/` pages; move the file to the root or extend the rule.
- [ ] Add regression tests for generated Windows commands and clean-clone skill checks #tests
  - Command escaping on Windows, including `%VAR%` in paths.
  - `check.sh` on a fresh clone.
