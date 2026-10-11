---
name: fleex-index
description: Find where a function, class, or Markdown section is and read only its lines, instead of reading whole files or grepping broadly: file outline with line ranges, one symbol or section, where a symbol is defined, which files mention a word, and a directory map with sizes. Use when exploring an unfamiliar repository, before opening a file over a few hundred lines, or when a Read was denied with an outline. Do not use for type-aware references, diagnostics, or refactoring.
---

# Index

In Claude Code the plugin's hook already denies the first whole read of a file over 400 lines and
returns its outline; read the ranges you need, or repeat the read for the whole file.

Run `scripts/index.py` (relative to this skill's directory) from anywhere in the repository with
Python 3.9+ (`python3`, or `python` on Windows). It needs only the standard library and `git`, and
reads tracked and untracked, non-ignored files. Path arguments are relative to the current
directory; output paths are relative to the repository root.

- `map [path] [--depth N]`: files and line counts per directory; start here in an unfamiliar
  repository.
- `outline <file>`: nested symbols or Markdown headings as `start-end kind name`.
- `show <file> <name> [--line N]`: the text of one symbol or section, with its decorators and doc
  comments; `name` may be qualified (`Class.method`, `Section.Subsection`).
- `find <name> [paths...]`: definitions of a symbol across the repository.
- `refs <name> [paths...]`: files that mention a whole word, most hits first, with line numbers.

Every command takes `--limit` (default 60 rows) and `--offset`; a trailer names the next offset.

## Requirements

If `python3` (`python` on Windows) or `git` is missing, tell the user what to install and use
bounded searches meanwhile. When the first output line reads `# patterns (ctags not found; ...)`,
the user can install Universal Ctags for exact symbols; tell them once per session, with the command
the line gives for their system.

## Accuracy

Code symbols come from Universal Ctags when it is installed, otherwise from per-language line
patterns; the first output line names the parser and why. Both use one kind vocabulary, and a
function directly inside a type is a `method`. Shell heredocs are symbols named by their delimiter;
text inside heredocs and Python triple-quoted strings never yields symbols. `--backend ctags` fails
without Universal Ctags; `--backend patterns` skips it. Ranges ctags leaves open are closed by
indentation. Markdown, TOML, and YAML top-level keys are always parsed exactly; code ranges are
hints. Unusual formatting, macros, or generated code can hide or misplace a symbol: when a result is
empty or surprising, fall back to a bounded search and read. `refs` matches text, so it includes
comments and strings and misses aliased imports. Use an LSP or the language's own tools when they
are available for type-aware references.
