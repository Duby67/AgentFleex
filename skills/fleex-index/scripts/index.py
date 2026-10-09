"""Token-cheap navigation for any git repository: map, outline, show, find, refs.

Standard library only. Code symbols come from Universal Ctags when it is installed, otherwise from
per-line patterns; ranges ctags leaves open are closed by indentation. Markdown, TOML, and YAML are
always parsed here. Output is plain text bounded by --limit; a trailer names the next --offset.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import io
import subprocess
import sys
import tokenize
from collections import defaultdict
from pathlib import Path
from typing import Any

MODIFIERS = (r"(?:(?:export|default|declare|pub(?:\([^)]*\))?|public|private|protected|internal|"
             r"static|abstract|final|async|override|virtual|sealed|partial|open|data|inline|"
             r"unsafe|extern|readonly|local|global|companion|@\w+(?:\([^)]*\))?)\s+)*")
KEYWORDS = (r"class|function|func|fn|interface|struct|enum|trait|impl|type|module|namespace|"
            r"record|object|protocol|extension|sub|proc|macro|union|def")
STATEMENTS = {"if", "for", "while", "switch", "catch", "return", "new", "else", "await", "throw",
              "using", "lock", "sizeof", "typeof", "do", "case", "goto", "delete", "yield"}
PYTHON = [re.compile(r"^(\s*)(?:async\s+)?(?P<kind>def|class)\s+(?P<name>\w+)")]
SHELL = [re.compile(r"^(\s*)(?:function\s+)?(?P<name>[A-Za-z_][\w-]*)\s*\(\)\s*[{(]"),
         re.compile(r"^(\s*)function\s+(?P<name>[A-Za-z_][\w-]*)")]
POWERSHELL = [re.compile(r"^(\s*)(?P<kind>function|filter|class|enum)\s+(?P<name>[\w-]+)",
                         re.IGNORECASE)]
SQL = [re.compile(r"^(\s*)create\s+(?:or\s+replace\s+)?(?P<kind>table|view|function|procedure|"
                  r"index|trigger|type)\s+(?:if\s+not\s+exists\s+)?(?P<name>[\w.\"]+)",
                  re.IGNORECASE)]
GENERIC = [
    # Go types report their concrete kind: type Server struct
    re.compile(r"^(\s*)type\s+(?P<name>\w+)\s+(?P<kind>struct|interface)\b"),
    # Go method receiver: func (r *T) Name(
    re.compile(r"^(\s*)func\s+\([^)]*\)\s*(?P<name>\w+)"),
    # Keyword definitions: export async function f, pub(crate) struct S, data class C.
    re.compile(rf"^(\s*){MODIFIERS}(?:(?:data|enum|sealed|case|abstract)\s+)?(?P<kind>{KEYWORDS})\s+"
               r"(?P<name>[A-Za-z_$][\w$]*)"),
    # Arrow or function expressions: const f = async (x) =>, let g = function
    re.compile(r"^(\s*)(?:export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*"
               r"(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)"),
]
# C-like methods: a return type before name(, with the body on this or a later line.
C_LIKE = GENERIC + [re.compile(r"^(\s*)(?P<first>[\w<>\[\],.?*&:]+)\s+(?:[\w<>\[\],.?*&:]+\s+)*\*?"
                               r"(?P<name>[A-Za-z_]\w*)\s*\([^;=]*$")]
# JavaScript and TypeScript class members: async get(id: string): Promise<T> {
JS = GENERIC + [re.compile(r"^(\s+)(?:(?:public|private|protected|static|async|readonly|override|"
                           r"get|set)\s+)*\*?(?P<first>)(?P<name>[A-Za-z_$#][\w$]*)\s*(?:<[^>]*>)?"
                           r"\([^;]*\)\s*(?::[^=;]+)?\{\s*$")]
SHELL_SUFFIXES = (".sh", ".bash", ".zsh", ".ksh")
# Files whose Python strings could not be tokenized, reported in the output header.
UNTOKENIZED: list[str] = []
HEREDOC = re.compile(r"(?<!<)<<(-?)\s*(['\"]?)([A-Za-z_]\w*)\2")
FAMILIES = {
    **dict.fromkeys((".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue",
                     ".svelte"), JS),
    **dict.fromkeys((".py", ".pyi"), PYTHON),
    **dict.fromkeys(SHELL_SUFFIXES, SHELL),
    **dict.fromkeys((".ps1", ".psm1"), POWERSHELL),
    ".sql": SQL,
    **dict.fromkeys((".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".java", ".kt", ".kts", ".scala",
                     ".swift", ".dart", ".php", ".m", ".mm", ".groovy"), C_LIKE),
}
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
TOML_TABLE = re.compile(r"^\s*\[\[?\s*([^\]]+?)\s*\]\]?")
YAML_KEY = re.compile(r"^([A-Za-z_][\w.-]*):(?:\s|$)")
PREFIX = ("@", "#[", "///", "//", "/*", "*", "#", "--")
# Ctags kinds that are not definitions with a body worth navigating to.
CTAGS_SKIP = {"field", "property", "variable", "local", "parameter", "enumerator", "label",
              "macroparam", "import", "unknown", "externvar", "alias", "package"}
# One vocabulary for both parsers; functions directly inside a type become methods.
KINDS = {"def": "function", "func": "function", "fn": "function", "sub": "function",
         "subroutine": "function", "proc": "function", "filter": "function", "method": "function",
         "singletonmethod": "function", "implementation": "impl", "typedef": "type"}
TYPES = {"class", "struct", "interface", "trait", "impl", "enum", "record", "object", "protocol",
         "extension", "union"}
INSTALL_CTAGS = ("for exact symbols install Universal Ctags: apt install universal-ctags, "
                 "brew install universal-ctags, or winget install UniversalCtags.Ctags")
MARKUP = {".md", ".markdown", ".mdx", ".toml", ".yaml", ".yml"}
SKIPPED = {".json", ".lock", ".svg", ".csv", ".txt", ".log", ".rst"}
TRAILING_COMMENT = re.compile(r"\s+(#|//).*$")
BOGUS_NAME = re.compile(r"[=\s()]")
CLOSER = re.compile(r"^\s*(\}|\)|\]|end\b|fi\b|done\b|esac\b)")


class Fail(Exception):
    pass


def git(root: Path, *args: str) -> str:
    # Exit code 1 means no match for git grep.
    return run(root, ["git", *args], ok=(0, 1))


def run(root: Path, command: list[str], ok: tuple[int, ...] = (0,)) -> str:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", check=False)
    if result.returncode not in ok:
        raise Fail(result.stderr.strip() or f"{command[0]} failed")
    return result.stdout


def git_names(root: Path, *args: str) -> list[str]:
    """Paths from a git command run with -z, which leaves special characters unquoted."""
    return [name for name in git(root, *args).split("\0") if name]


def read_lines(path: Path) -> list[str]:
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        raise Fail(f"{path}: binary file")
    return data.decode("utf-8", errors="replace").splitlines()


def indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def pattern_symbols(lines: list[str], patterns: list[re.Pattern]) -> list[list]:
    symbols = []
    for number, line in enumerate(lines, 1):
        for pattern in patterns:
            match = pattern.match(line)
            if not match:
                continue
            fields = match.groupdict()
            if "first" in fields and {fields["name"], fields["first"]} & STATEMENTS:
                break
            name = fields["name"]
            kind = fields.get("kind") or "def"
            symbols.append([number, 0, kind.lower(), name, indent(line)])
            break
    return symbols


def close(lines: list[str], symbols: list[list], verbatim: frozenset = frozenset()) -> list[list]:
    """Fill missing ends by indentation and widen starts over decorators and doc comments.

    Lines in `verbatim` (heredoc bodies) never end a symbol.
    """
    for symbol in symbols:
        start, level = symbol[0], symbol[4]
        if not symbol[1]:
            symbol[1] = indented_end(lines, start, level, verbatim)
        while start > 1 and indent(lines[start - 2]) == level and \
                lines[start - 2].strip().startswith(PREFIX):
            start -= 1
        symbol[0] = start
    return symbols


def indented_end(lines: list[str], start: int, level: int, verbatim: frozenset) -> int:
    end = len(lines)
    for number in range(start + 1, len(lines) + 1):
        line = lines[number - 1]
        if not line.strip() or indent(line) > level or number in verbatim:
            continue
        stripped = line.strip()
        # Continuations of the signature or an opening brace on its own line.
        opens = TRAILING_COMMENT.sub("", stripped).endswith(("{", ":", "(", "["))
        if stripped == "{" or (CLOSER.match(line) and opens):
            continue
        # A closer at the symbol's own level ends its block; a shallower one belongs to a parent.
        end = number if CLOSER.match(line) and indent(line) == level else number - 1
        break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return max(end, start)


def markdown_symbols(lines: list[str]) -> list[list]:
    heads: list[list[Any]] = []
    fenced = False
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced and (match := HEADING.match(line)):
            level = len(match.group(1))
            heads.append([number, 0, f"h{level}", match.group(2), level])
    for i, head in enumerate(heads):
        later = [h[0] for h in heads[i + 1:] if h[4] <= head[4]]
        head[1] = (later[0] - 1) if later else len(lines)
        while head[1] > head[0] and not lines[head[1] - 1].strip():
            head[1] -= 1
    return heads


def key_symbols(lines: list[str], pattern: re.Pattern, kind: str) -> list[list]:
    starts = [(n, m.group(1)) for n, line in enumerate(lines, 1) if (m := pattern.match(line))]
    result = []
    for i, (number, name) in enumerate(starts):
        end = starts[i + 1][0] - 1 if i + 1 < len(starts) else len(lines)
        result.append([number, end, kind, name, 0])
    return result


@functools.lru_cache(maxsize=None)
def ctags_missing() -> str:
    """Why Universal Ctags cannot be used, or an empty string when it can."""
    try:
        version = subprocess.run(["ctags", "--version"], capture_output=True, text=True,
                                 check=False).stdout
        features = subprocess.run(["ctags", "--list-features"], capture_output=True,
                                  text=True, check=False).stdout
    except OSError:
        return "ctags not found"
    if "Universal Ctags" not in version:
        return "ctags is not Universal Ctags"
    if not re.search(r"^json\b", features, re.MULTILINE):
        return "ctags lacks JSON output"
    return ""


def ctags_symbols(root: Path, names: list[str]) -> dict[str, list[list]]:
    """Ctags rows per file for the files whose language ctags knows."""
    languages = run(root, ["ctags", "--print-language", *names])
    known = [line.rpartition(": ")[0] for line in languages.splitlines()
             if not line.endswith(": NONE")]
    if not known:
        return {}
    output = run(root, ["ctags", "--sort=no", "--output-format=json", "--fields=+neKZl",
                             "--extras=-F", "-o", "-", *known])
    rows: dict[str, list[list]] = {name: [] for name in known}
    for line in output.splitlines():
        tag = json.loads(line)
        if tag.get("_type") != "tag" or tag["kind"] in CTAGS_SKIP or BOGUS_NAME.search(tag["name"]):
            continue
        kind = tag["kind"]
        # Python namespaces are import aliases, and lambdas are values, not definitions.
        if tag.get("language") == "Python" and (
                kind == "namespace" or re.search(r"=\s*lambda\b", tag.get("pattern", ""))):
            continue
        # Python methods are "member"; elsewhere a member is a field, which patterns skip too.
        if kind == "member":
            if tag.get("language") != "Python":
                continue
            kind = "function"
        # Constants count only when they hold a function, as the arrow pattern finds them.
        if kind == "constant":
            if not re.search(r"=>|\bfunction\b", tag.get("pattern", "")):
                continue
            kind = "function"
        rows[tag["path"]].append([tag["line"], tag.get("end", 0), kind, tag["name"], 0])
    for name, found in rows.items():
        lines = read_lines(root / name)
        for row in found:
            row[4] = indent(lines[row[0] - 1])
        found[:], verbatim = drop_verbatim(name, lines, found)
        normalize(close(lines, found, verbatim))
    return rows


def drop_verbatim(name: str, lines: list[str], rows: list[list]) -> tuple[list[list], frozenset]:
    """Sorted rows without anything found in verbatim text, and the verbatim line numbers.

    Verbatim text is heredoc bodies in shell files, which become heredoc rows, and triple-quoted
    strings in Python files.
    """
    docs: list[list[Any]] = []
    body: frozenset[int] = frozenset()
    if name.lower().endswith(SHELL_SUFFIXES):
        docs = heredocs(lines)
        body = frozenset(n for d in docs for n in range(d[0] + 1, d[1] + 1))
    elif name.lower().endswith((".py", ".pyi")):
        body = python_strings(name, lines)
    kept = [row for row in rows if row[2] != "heredoc" and row[0] not in body]
    return sorted(kept + docs, key=lambda row: row[0]), body


def python_strings(name: str, lines: list[str]) -> frozenset:
    """Lines after the first line of a multi-line string, through its last line."""
    inside: set[int] = set()
    starts: list[int] = []
    source = io.StringIO("\n".join(lines) + "\n").readline
    try:
        for token in tokenize.generate_tokens(source):
            # Python 3.12+ splits f-strings into FSTRING_START ... FSTRING_END tokens.
            kind = tokenize.tok_name[token.type]
            if kind == "FSTRING_START":
                starts.append(token.start[0])
            elif kind in ("STRING", "FSTRING_END"):
                first = starts.pop() if kind == "FSTRING_END" else token.start[0]
                inside.update(range(first + 1, token.end[0] + 1))
    except (tokenize.TokenError, SyntaxError):
        UNTOKENIZED.append(name)
    return frozenset(inside)


def heredocs(lines: list[str]) -> list[list]:
    """One row per heredoc, named by its delimiter, ending on the delimiter line."""
    docs, number = [], 1
    while number <= len(lines):
        match = HEREDOC.search(lines[number - 1])
        if match:
            end = next((n for n in range(number + 1, len(lines) + 1)
                        if lines[n - 1].strip() == match.group(3)), len(lines))
            docs.append([number, end, "heredoc", match.group(3), indent(lines[number - 1])])
            number = end
        number += 1
    return docs


def normalize(rows: list[list]) -> list[list]:
    """Map parser-specific kinds to one vocabulary and name functions inside types methods."""
    stack: list[list[Any]] = []
    for row in rows:
        row[2] = KINDS.get(row[2].lower(), row[2].lower())
        while stack and not (stack[-1][0] < row[0] <= stack[-1][1]):
            stack.pop()
        if row[2] == "function" and stack and stack[-1][2] in TYPES:
            row[2] = "method"
        stack.append(row)
    return rows


def own_symbols(path: Path) -> list[list]:
    lines = read_lines(path)
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".mdx"}:
        return markdown_symbols(lines)
    if suffix == ".toml":
        return key_symbols(lines, TOML_TABLE, "table")
    if suffix in {".yaml", ".yml"}:
        return key_symbols(lines, YAML_KEY, "key")
    if suffix in SKIPPED:
        return []
    rows = pattern_symbols(lines, FAMILIES.get(suffix, GENERIC))
    rows, verbatim = drop_verbatim(path.name, lines, rows)
    return normalize(close(lines, rows, verbatim))


def symbols(root: Path, names: list[str], backend: str) -> tuple[dict[str, list[list]], str]:
    """Rows of [start, end, kind, name, level] per file, and a note on which parser ran."""
    code = [n for n in names if Path(n).suffix.lower() not in MARKUP | SKIPPED]
    by_ctags = ctags_symbols(root, code) if backend == "ctags" and code else {}
    result = {}
    for name in names:
        try:
            result[name] = by_ctags[name] if name in by_ctags else own_symbols(root / name)
        except (Fail, OSError):
            continue
    patterned = [n for n in code if n not in by_ctags]
    if backend != "ctags":
        reason = f"{ctags_missing()}; {INSTALL_CTAGS}" if ctags_missing() else "requested"
        note = f"patterns ({reason})" if code else "markup"
    elif patterned:
        note = f"ctags; patterns for {len(patterned)} file(s) ctags cannot parse"
    else:
        note = "ctags" if code else "markup"
    if UNTOKENIZED:
        note += f"; strings not detected in {len(UNTOKENIZED)} file(s) Python cannot tokenize"
    return result, note


def qualified(rows: list[list]) -> list[str]:
    """Dotted names through enclosing symbols: Class.method, Section.Subsection."""
    stack: list[tuple[list[Any], str]] = []
    names: list[str] = []
    for row in rows:
        while stack and not (stack[-1][0][0] < row[0] <= stack[-1][0][1]):
            stack.pop()
        names.append(f"{stack[-1][1]}.{row[3]}" if stack else row[3])
        stack.append((row, names[-1]))
    return names


def page(rows: list[str], limit: int, offset: int) -> str:
    shown = rows[offset:offset + limit]
    rest = len(rows) - offset - len(shown)
    if rest > 0:
        shown.append(f"... {rest} more; use --offset {offset + len(shown)}")
    return "\n".join(shown) if shown else "(no results)"


def depths(rows: list[list]) -> list[int]:
    stack: list[list[Any]] = []
    result: list[int] = []
    for row in rows:
        while stack and not (stack[-1][0] < row[0] <= stack[-1][1]):
            stack.pop()
        result.append(len(stack))
        stack.append(row)
    return result


def cmd_map(root: Path, args) -> list[str]:
    base = args.path or ""
    files = git_names(root, "ls-files", "-z", "-co", "--exclude-standard", "--", base or ".")
    if not files:
        raise Fail(f"no files under {base or '.'}")
    totals: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    prefix = len(Path(base).parts)
    for name in files:
        parts = Path(name).parts
        key = "/".join(parts[:prefix + args.depth])
        if len(parts) > prefix + args.depth:
            key += "/"
        try:
            data = (root / name).read_bytes()
        except OSError:
            continue
        totals[key][0] += 1
        totals[key][1] += 0 if b"\0" in data[:8192] else data.count(b"\n")
    return [f"{key}  {count} files, {lines} lines" if key.endswith("/") else f"{key}  {lines} lines"
            for key, (count, lines) in sorted(totals.items())]


def cmd_outline(root: Path, args) -> list[str]:
    found, note = symbols(root, [args.file], args.backend)
    rows = found.get(args.file, [])
    return [f"# {note}"] + [f"{'  ' * d}{r[0]}-{r[1]} {r[2]} {r[3]}"
                            for r, d in zip(rows, depths(rows))]


def cmd_show(root: Path, args) -> list[str]:
    path = root / args.file
    found, note = symbols(root, [args.file], args.backend)
    rows = found.get(args.file, [])
    matches = [r for r, q in zip(rows, qualified(rows))
               if args.name in (r[3], q) or q.endswith(f".{args.name}")
               if not args.line or r[0] == args.line]
    if not matches:
        raise Fail(f"{args.file}: no symbol or heading named {args.name!r}; run outline")
    if len(matches) > 1:
        raise Fail(f"{args.file}: {args.name!r} is ambiguous at lines "
                   f"{', '.join(str(r[0]) for r in matches)}; pass --line")
    start, end = matches[0][:2]
    return [f"{args.file}:{start}-{end} # {note}", *read_lines(path)[start - 1:end]]


def cmd_find(root: Path, args) -> list[str]:
    names = git_names(root, "grep", "-z", "--untracked", "-I", "-l", "-w", "-F", "-e", args.name,
                      "--", *args.paths)
    found, note = symbols(root, names, args.backend)
    rows = [f"{name}:{r[0]}-{r[1]} {r[2]} {r[3]}"
            for name in names for r in found.get(name, []) if r[3] == args.name]
    return [f"# {note}"] + rows


def cmd_refs(root: Path, args) -> list[str]:
    hits = defaultdict(list)
    output = git(root, "grep", "-z", "--untracked", "-I", "-n", "-w", "-F", "-e", args.name,
                 "--", *args.paths)
    # With -z each hit is one line of "path\0number\0text".
    for record in output.splitlines():
        name, number, _ = record.split("\0", 2)
        hits[name].append(number)
    return [f"{name}: {len(lines)} ({', '.join(lines[:8])}{', ...' if len(lines) > 8 else ''})"
            for name, lines in sorted(hits.items(), key=lambda item: -len(item[1]))]


def main() -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="repository root (default: current directory)")
    common.add_argument("--limit", type=int, default=60, help="maximum output rows")
    common.add_argument("--offset", type=int, default=0, help="rows to skip")
    common.add_argument("--backend", choices=("auto", "ctags", "patterns"), default="auto",
                        help="code symbol parser (default: ctags if Universal Ctags is found)")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    add = lambda name, text: sub.add_parser(name, help=text, parents=[common])  # noqa: E731
    p = add("map", "tracked files and sizes per directory")
    p.add_argument("path", nargs="?")
    p.add_argument("--depth", type=int, default=1)
    p = add("outline", "symbols or headings of one file with line ranges")
    p.add_argument("file")
    p = add("show", "print one symbol or Markdown section")
    p.add_argument("file")
    p.add_argument("name")
    p.add_argument("--line", type=int, help="start line to pick among duplicates")
    for name, text in (("find", "where a symbol is defined"),
                       ("refs", "files that mention a word")):
        p = add(name, text)
        p.add_argument("name")
        p.add_argument("paths", nargs="*", help="limit the search to these paths")
    args = parser.parse_args()
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    here = Path(args.root).resolve()
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=here, capture_output=True,
                             text=True, check=False)
        if top.returncode:
            raise Fail(f"{here} is not inside a git repository; pass --root")
        root = Path(top.stdout.strip()).resolve()
        # Path arguments are relative to the current directory; git runs from the root.
        relative = lambda p: (here / p).resolve().relative_to(root).as_posix()  # noqa: E731
        for name in ("file", "path"):
            if getattr(args, name, None):
                setattr(args, name, relative(getattr(args, name)))
        if getattr(args, "paths", None):
            args.paths = [relative(p) for p in args.paths]
        if args.backend == "ctags" and ctags_missing():
            raise Fail(f"{ctags_missing()}; {INSTALL_CTAGS}, or use --backend patterns")
        if args.backend == "auto":
            args.backend = "patterns" if ctags_missing() else "ctags"
        rows = globals()[f"cmd_{args.command}"](root, args)
    except (Fail, OSError, ValueError) as error:
        print(f"index: {error}", file=sys.stderr)
        return 1
    if args.command in ("show", "outline", "find"):
        print(rows[0])
        print(page(rows[1:], args.limit, args.offset))
    else:
        print(page(rows, args.limit, args.offset))
    return 0


if __name__ == "__main__":
    sys.exit(main())
