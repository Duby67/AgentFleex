# TODO

`TODO.md` is a durable backlog of known defects, risks, and planned work that people and agents
both read: every item must stay true, findable, and actionable without the conversation that
produced it. It is not for TODO comments in code or an external issue tracker.

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

- Under `# TODO` comes only the legend of states and tags: no scope, review date, or format rules.
- Sections are priorities (`## P0` most urgent) unless the file already groups another way; keep
  an existing grouping. Item order inside a section is priority. The lowest priority is the
  backlog. Omit empty sections; add no `# DONE` or `# BACKLOG`.
- Item line: one imperative action, then `#tags` from the legend; add a new tag to the legend
  first. `@name` assigns an owner, `#123` or a URL refers to an issue.
- Nested lines hold the evidence and open decisions: why it matters, relative links to code as
  `[file:line](path#Lx-Ly)`, the command that shows it. No prose paragraphs.

## Rules

- Add only what you verified: a reproduced failure, a read line of code, a failing check. Mark a
  suspicion as such in its nested line.
- One item per independent fix; merge duplicates, and link an existing issue instead of copying it.
- An item is not permission to change code. Work on one only when the user asks for it.
- Remove a finished item only after the fix is in place and the checks that prove it ran after the
  last change; git history records it.
- Record completed work in `CHANGELOG.md` as the solved problem and resulting behavior, without
  mentioning `TODO.md` or its item closure. Do not duplicate an existing changelog entry.
- A declined item stays in place as `- [-]` with a nested line saying why, so the same finding is
  not raised again.
- When the user decides an open question, record the decision and drop the alternatives.
- When code moves, update the line links of items that point to it; a stale line link is a defect.
- Create `docs/TODO.md` only when the user asks for a TODO list, and ask whether it should be
  committed or listed in `.gitignore`; an existing `TODO.md` stays where it is.

## Check

After the skill's check, open each changed `#L` link target and confirm the lines still show what
the item says.
