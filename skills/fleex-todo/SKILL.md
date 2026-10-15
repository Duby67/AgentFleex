---
name: fleex-todo
description: Maintain a repository's TODO.md backlog of known defects, risks, and planned work: add findings with evidence, prioritize, tag, keep code links current, and close or decline items. Use when the user asks to record review findings or tasks in TODO.md, to update, reprioritize, or clean up it, or to work through or close its items. Do not use for TODO comments in code, an external issue tracker, or the agent's own in-session task list.
---

# TODO

`TODO.md` at the repository root is a durable backlog that people and agents both read: every item
must stay true, findable, and actionable without the conversation that produced it.

## Format

Uses the checkboxes of [todo-md](https://github.com/todo-md/todo-md):

```markdown
# TODO

States: `- [ ]` open, `- [-]` declined.
Tags: `#bug`, `#security`, `#reliability`, `#ci`, `#tests`, `#chore`.

## P0 — blocks a release

- [ ] Fix the stop hook dropping non-ASCII file names #bug
  - `changed()` calls `git diff` without `-z`, so `is_file()` fails on quoted names
    ([hook.py:92-99](hooks/hook.py#L92-L99)).

## P3 — maintenance

- [-] Declined item #security
  - Why it was declined.
```

- Under `# TODO` comes only the legend of states and tags: no scope, review date, or description
  of the format.
- States: `- [ ]` open, `- [-]` declined. Item order inside a section is priority.
- Sections under `# TODO` are priorities (`## P0` most urgent) unless the file already groups
  another way; keep an existing grouping. The lowest priority is the backlog. Omit empty sections,
  and do not add `# DONE` or `# BACKLOG` sections.
- Item line: one imperative action, then `#tags`; use the tags the legend lists and add a new one
  to the legend first. `@name` assigns an owner, `#123` or a URL refers to an issue.
- Nested lines hold the evidence and open decisions: why it matters, relative links to code as
  `[file:line](path#Lx-Ly)`, the command that shows it. No prose paragraphs.
- `TODO.md` is a human doc written in English. Translations may lag: mark stale copies with an
  outdated note linking the English source. Use $fleex-i18n only for a requested translation pass.

## Rules

- Add only what you verified: a reproduced failure, a read line of code, a failing check. Mark a
  suspicion as such in its nested line instead of stating it as fact.
- One item per independent fix; merge duplicates, and link an existing issue instead of copying it.
- An item is not permission to change code. Work on one only when the user asks for it.
- Remove a finished item only after the fix is in place and the checks that prove it ran after the
  last change; git history records it.
- Use the backlog as a local task checklist. Record completed work in `CHANGELOG.md` as the solved
  problem and resulting behavior, without mentioning or linking `TODO.md` or describing its
  cleanup, item closure, or reopening. Do not duplicate an existing changelog entry for the fix.
- A declined item stays in place as `- [-]` with a nested line saying why, so the same finding is
  not raised again.
- When the user decides an open question, record the decision and drop the alternatives.
- When code moves, update the line links of items that point to it; a link to a stale line is a
  defect in the list.
- Creating `TODO.md` adds a root file: do it only when the user asks for a TODO list, and ask
  whether it should be committed or listed in `.gitignore`.

## Check

From the repository root, run `../fleex-skills/scripts/check.sh` relative to this skill's directory
(`check.ps1` on Windows) to verify relative links, then open each changed `#L` link target and
confirm the lines still show what the item says.
