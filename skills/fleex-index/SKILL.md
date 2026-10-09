---
name: fleex-index
description: Navigate any git repository cheaply with a dependency-free script: directory map with sizes, file outline with symbol and heading line ranges, one symbol or Markdown section, where a symbol is defined, and which files mention a word. Use before reading large files or searching broadly for code, config, or docs. Do not use for type-aware references, diagnostics, or refactoring.
---

# Index

Run `scripts/index.py` (relative to this skill's directory) from anywhere in the repository with
Python 3.8+ (`python3`, or `python` on Windows). It needs only the standard library and `git`, and
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

Symbols come from per-language line patterns and indentation, not a parser. Markdown, TOML, and
YAML top-level keys are exact; code ranges are hints. Unusual formatting, macros, or generated code
can hide or misplace a symbol: when a result is empty or surprising, fall back to a bounded search
and read. `refs` matches text, so it includes comments and strings and misses aliased imports. Use
an LSP or the language's own tools when they are available for type-aware references.
