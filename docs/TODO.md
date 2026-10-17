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
