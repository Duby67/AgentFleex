# TODO

**English** · [Русский](ru/TODO.md)

States: `- [ ]` open, `- [-]` declined.
Tags: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

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
    ([.pre-commit-config.yaml](../.pre-commit-config.yaml)), `docs/CHANGELOG.md` with
    `## [x.y.z](tag link)` and a brief list, CI tags and releases only a new version from `develop`
    ([ci.yml](../.github/workflows/ci.yml)); the steps are in
    [CONTRIBUTING](CONTRIBUTING.md#versions-and-releases).
  - Decide for GitLab: release through CI or tags only.
- [ ] Add `fleex-hygiene` defaults for Markdown, YAML, JSON, and `.editorconfig` #feature
  - Defaults exist only for Ruff, mypy, and ShellCheck
    ([checks.py:251-282](../skills/fleex-hygiene/scripts/checks.py#L251-L282)).
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
- [ ] Decide how `.github/SECURITY.md` is translated #docs
  - Human docs are translated to ru, but `check.sh` and `fleex-docs` accept translations only of
    root files and `docs/` pages; move the file to `docs/`, where GitHub also finds it, as was done
    for `CONTRIBUTING.md`, or extend the rule.
- [ ] Add regression tests for generated Windows commands and clean-clone skill checks #tests
  - Command escaping on Windows.
  - `check.sh` on a fresh clone.
