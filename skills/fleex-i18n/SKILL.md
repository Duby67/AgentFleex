---
name: fleex-i18n
description: User-invoked translation of human documentation under docs/<code>/, with language switchers and outdated notes. Use only when the user requests translations, language changes, or a translation pass before a PR. Translation lag during development is allowed. Do not invoke automatically when English docs change, for agent-facing files, or to check docs against code.
disable-model-invocation: true
---

# Translations

English is the source of every human document. Translations are optional copies under `docs/`, so
a language can be added or removed without touching the English files.

## When

- A repository is multilingual once the Language section of `AGENTS.md` lists languages by
  BCP 47 code (`ru`, `pt-BR`, `zh-CN`): `Human docs are in English, translated to: ru, zh-CN; ...`.
- Never start translations on your own. Make a repository multilingual, or add a language, only
  when the user asks for it directly; then add or extend `translated to:` in that line.
- Run translation passes only on request, including a requested pass before a PR. During normal
  development translations may lag, and new English docs may wait for that pass. Existing
  translations get an outdated note when their English source changes.
- During a translation pass, cover every listed language for the requested docs; before a PR,
  check all changed human docs for missing or stale translations.
- Agent-facing files (`AGENTS.md`, `.claude/CLAUDE.md`, skills, agent docs) are never translated.

## Layout

- English files stay in place without a suffix; `docs/` never gains an `en/` folder.
- Every translation lives under `docs/<code>/`, never in the root or beside its original: a root
  file by name (`README.md` → `docs/ru/README.md`), a `docs/` page at its path inside `docs/`
  (`docs/api/auth.md` → `docs/ru/api/auth.md`).
- When a root file and a `docs/` page share a name, `docs/<code>/<name>` translates the one its
  switcher links to; translate only one of them.
- Links in a translation point to translations where they exist, otherwise to English. Shared
  images stay shared; copy one only to translate text inside it. No stubs or placeholder pages.

## Switcher

Every file of a set (an English original and its existing translations) has one line right under its first
heading that links to all the others. Each language is named in itself, the current one is bold
and unlinked, English comes first, then the order of `AGENTS.md`. In `README.md`:

```markdown
**English** · [Русский](docs/ru/README.md)
```

Adding or removing a translation updates the line in every file of the set.

## Changes

- Change English first; a translation never states what English does not.
- During a requested pass, update each translation faithfully. Until that pass, put a note under
  the switcher of each stale translation, in its language, linking the English original:
  `> Перевод отстаёт от [английской версии](../../README.md).` Remove the note once caught up.
- Translate meaning, not words. Keep code, commands, paths, identifiers, and link targets as they
  are.

## Remove a language

Delete `docs/<code>/`, the language in every switcher, and its code in `AGENTS.md`. Drop a switcher
line left with English alone, and `, translated to: ...` with the last language.

## Check

From the repository root, run `../fleex-skills/scripts/check.sh` relative to this skill's directory
(`check.ps1` on Windows): for each language in `AGENTS.md` it verifies that translations live under
`docs/<code>/` with an English original and that every file of a set links to all the others.
