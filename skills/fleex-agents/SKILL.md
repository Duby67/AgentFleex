---
name: fleex-agents-optimize
description: Optimize the content of AGENTS.md for token cost and clarity: add missing token-saving rules, tighten existing rules without changing their meaning, and remove what agents do by default, facade, and decoration. Use when asked to write, optimize, shorten, compress, or clean up AGENTS.md rules. Do not use for CLAUDE.md, skill wiring, or skill content.
---

# Optimize AGENTS.md

`AGENTS.md` is paid for on every model request; each line must change what the agent does. Wiring
and the starter template belong to `$fleex-agents-md`.

It holds only what every task needs and the agent cannot infer: one or two sentences on what the
project is and is not, hard invariants whose violation is costly, and pointers to canonical owners
the agent would not find on its own.

## Keep the owner's rules

The repository owner's rules are decisions, not drafts. Change their form, never their meaning:

- shorten wording, merge duplicates, and turn prose into one imperative line, keeping every
  condition, exception, and named path, command, or tool;
- never weaken, widen, or reorder priorities of a rule, and never invent rationale for it;
- when a rule looks wrong, obsolete, or contradicts code or another rule, keep it and report it;
- move a long task-specific procedure to a skill only with the user's consent.

## Remove

- Default agent behavior: "write clean code", "follow best practices", "read code before changing
  it", "write tests", "think step by step", "be careful", "don't make things up", role-play ("you
  are a senior engineer").
- Facts the agent infers cheaply from the repository: the language or framework visible in manifests,
  the directory tree, what a well-named file contains.
- Copies of facts owned elsewhere (link instead) and explanations for humans (move to docs).
- Facade: a line about the file itself, even inside a rule ("this file is loaded on every request"), a table of contents, badges, a closing summary,
  restated headings, rationale and history that change no behavior.
- Decoration: emoji, bold or ALL-CAPS emphasis, "IMPORTANT"/"CRITICAL"/"MUST" markers, horizontal
  rules, nested headings over one bullet, tables that are lists. Strong emphasis makes current models
  overapply a rule; plain imperative wording is enough.

## Add

Add missing rules from [token rules](references/token-rules.md) that fit this repository, filled
with its real commands and paths. Verify every command and path before writing it; skip a rule you
cannot make concrete.

## Gotchas

- A rule that looks like default behavior may encode a past incident ("never run migrations
  locally"); if it names something specific to the repository, it stays.
- Rules that only one client honors are still rules; do not drop them for portability.

## Check

Report each removed line with its reason, so the owner can restore it. Compare `wc -w AGENTS.md`
before and after. For each added or edited line, ask whether an agent would act differently without
it; if not, delete it. From the repository root, run `../fleex-skills/scripts/check.sh` relative to
this skill's directory (`check.ps1` on Windows) and fix every reported error.
