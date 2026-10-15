# TODO

**English** · [Русский](ru/TODO.md)

States: `- [ ]` open, `- [-]` declined.
Tags: `#bug`, `#security`, `#reliability`, `#feature`, `#tokens`, `#ci`, `#tests`, `#docs`,
`#chore`.

## P3 — features

- [ ] Extend read savings beyond the Read tool #tokens
  - The hook matches only `Read` ([hooks.json:6](../hooks/hooks.json#L6)); `cat`, `grep -r`, and
    long Bash output bypass it.
- [ ] Automate skill activation tests #tests
  - [fleex-skills](../skills/fleex-skills/SKILL.md#L98) describes about ten manual prompts per
    skill; check whether `claude plugin eval` fits.
- [ ] Add a CI check of the always-loaded token budget #tokens
  - `AGENTS.md` plus all skill descriptions; guards growth, not the current size.

## P4 — maintenance

- [ ] Remove the duplicated logic of `check.sh` and `check.ps1` or add an equivalence test #chore
- [ ] Add regression tests for generated Windows commands and clean-clone skill checks #tests
  - Command escaping on Windows.
  - `check.sh` on a fresh clone.
