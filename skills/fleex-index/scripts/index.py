"""Token-cheap navigation for any git repository: map, outline, show, find, refs.

Standard library only. Symbols come from per-line patterns and indentation, not a parser, so results
are navigation hints. Output is plain text bounded by --limit; a trailer names the next --offset.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

MODIFIERS = (r"(?:(?:export|default|declare|pub(?:\([^)]*\))?|public|private|protected|internal|"
             r"static|abstract|final|async|override|virtual|sealed|partial|open|data|inline|"
             r"unsafe|extern|readonly|local|global|companion|@\w+(?:\([^)]*\))?)\s+)*")
KEYWORDS = (r"class|function|func|fn|interface|struct|enum|trait|impl|type|module|namespace|"
            r"record|object|protocol|extension|sub|proc|macro|union|def")
STATEMENTS = {"if", "for", "while", "switch", "catch", "return", "new", "else", "await", "throw",
              "using", "lock", "sizeof", "typeof", "do", "case", "goto", "delete", "yield"}
PYTHON = [re.compile(r"^(\s*)(?:async\s+)?(?P<kind>def|class)\s+(?P<name>\w+)")]
SHELL = [re.compile(r"^(\s*)(?:function\s+)?(?P<name>[A-Za-z_][\w-]*)\s*\(\)\s*(?:\{.*)?$"),
         re.compile(r"^(\s*)function\s+(?P<name>[A-Za-z_][\w-]*)")]
POWERSHELL = [re.compile(r"^(\s*)(?P<kind>function|filter|class|enum)\s+(?P<name>[\w-]+)", re.I)]
SQL = [re.compile(r"^(\s*)create\s+(?:or\s+replace\s+)?(?P<kind>table|view|function|procedure|"
                  r"index|trigger|type)\s+(?:if\s+not\s+exists\s+)?(?P<name>[\w.\"]+)", re.I)]
GENERIC = [
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
FAMILIES = {
    **dict.fromkeys((".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue", ".svelte"),
                    JS),
    **dict.fromkeys((".py", ".pyi"), PYTHON),
    **dict.fromkeys((".sh", ".bash", ".zsh", ".ksh"), SHELL),
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
CLOSER = re.compile(r"^\s*(\}|\)|\]|end\b|fi\b|done\b|esac\b)")


class Fail(Exception):
    pass


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    if result.returncode not in (0, 1):
        raise Fail(result.stderr.strip() or f"git {args[0]} failed")
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


def code_symbols(lines: list[str], patterns: list[re.Pattern]) -> list[list]:
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
    for symbol in symbols:
        start, level = symbol[0], symbol[4]
        end = len(lines)
        for number in range(start + 1, len(lines) + 1):
            line = lines[number - 1]
            if not line.strip() or indent(line) > level:
                continue
            stripped = line.strip()
            # Continuations of the signature or an opening brace on its own line.
            if stripped == "{" or (CLOSER.match(line) and stripped.endswith(("{", ":"))):
                continue
            end = number if CLOSER.match(line) else number - 1
            break
        while end > start and not lines[end - 1].strip():
            end -= 1
        symbol[1] = end
        while start > 1 and indent(lines[start - 2]) == level and \
                lines[start - 2].strip().startswith(PREFIX):
            start -= 1
        symbol[0] = start
    return symbols


def markdown_symbols(lines: list[str]) -> list[list]:
    heads, fenced = [], False
    for number, line in enumerate(lines, 1):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced and (match := HEADING.match(line)):
            heads.append([number, 0, f"h{len(match.group(1))}", match.group(2), len(match.group(1))])
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


def symbols(path: Path) -> list[list]:
    """Rows of [start, end, kind, name, level], ordered by start line."""
    lines = read_lines(path)
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown", ".mdx"}:
        return markdown_symbols(lines)
    if suffix == ".toml":
        return key_symbols(lines, TOML_TABLE, "table")
    if suffix in {".yaml", ".yml"}:
        return key_symbols(lines, YAML_KEY, "key")
    if suffix in {".json", ".lock", ".svg", ".csv"}:
        return []
    return code_symbols(lines, FAMILIES.get(suffix, GENERIC))


def qualified(rows: list[list]) -> list[str]:
    """Dotted names through enclosing symbols: Class.method, Section.Subsection."""
    stack, names = [], []
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
    stack, result = [], []
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
    totals = defaultdict(lambda: [0, 0])
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
    rows = symbols(root / args.file)
    return [f"{'  ' * d}{r[0]}-{r[1]} {r[2]} {r[3]}" for r, d in zip(rows, depths(rows))]


def cmd_show(root: Path, args) -> list[str]:
    path = root / args.file
    rows = symbols(path)
    matches = [r for r, q in zip(rows, qualified(rows))
               if args.name in (r[3], q) or q.endswith(f".{args.name}")
               if not args.line or r[0] == args.line]
    if not matches:
        raise Fail(f"{args.file}: no symbol or heading named {args.name!r}; run outline")
    if len(matches) > 1:
        raise Fail(f"{args.file}: {args.name!r} is ambiguous at lines "
                   f"{', '.join(str(r[0]) for r in matches)}; pass --line")
    start, end = matches[0][:2]
    return [f"{args.file}:{start}-{end}", *read_lines(path)[start - 1:end]]


def cmd_find(root: Path, args) -> list[str]:
    rows = []
    names = git_names(root, "grep", "-z", "--untracked", "-I", "-l", "-w", "-F", "-e", args.name,
                      "--", *args.paths)
    for name in names:
        try:
            found = [r for r in symbols(root / name) if r[3] == args.name]
        except (Fail, OSError):
            continue
        rows += [f"{name}:{r[0]}-{r[1]} {r[2]} {r[3]}" for r in found]
    return rows


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
    for name, text in (("find", "where a symbol is defined"), ("refs", "files that mention a word")):
        p = add(name, text)
        p.add_argument("name")
        p.add_argument("paths", nargs="*", help="limit the search to these paths")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    here = Path(args.root).resolve()
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=here, capture_output=True,
                             text=True)
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
        rows = globals()[f"cmd_{args.command}"](root, args)
    except (Fail, OSError, ValueError) as error:
        print(f"index: {error}", file=sys.stderr)
        return 1
    if args.command == "show":
        print(rows[0])
        print(page(rows[1:], args.limit, args.offset))
    else:
        print(page(rows, args.limit, args.offset))
    return 0


if __name__ == "__main__":
    sys.exit(main())
