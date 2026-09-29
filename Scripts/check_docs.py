"""Check documentation paths, links, skill references and navigation."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = (
    "AGENTS.md",
    "README.md",
    "TODO.md",
    "Tests/README.md",
    "Docs/README.md",
    "Docs/GIT_WORKFLOW.md",
)
SKILLS_DIR = "Skills"
# Local-only files that documentation legitimately names but Git never tracks.
LOCAL_ONLY_PATHS = frozenset({".agents/tasks.md", ".agents/handoff.md"})
# A code span is a repository path when its first segment is a top-level directory.
REPOSITORY_PATH_PATTERN = re.compile(r"`(([A-Za-z0-9._-]+)/[^`\s]+)`")
PATH_PLACEHOLDER_CHARACTERS = frozenset("<>*{}$")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
SKILL_REFERENCE_PATTERN = re.compile(r"\$([a-z0-9]+(?:-[a-z0-9]+)+)")
TODO_BACKLOG_MARKER = "не источник текущего поведения"


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def add_error(errors: list[str], message: str) -> None:
    errors.append(f"- {message}")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def governed_markdown_paths() -> list[Path]:
    paths = [ROOT / name for name in ("AGENTS.md", "README.md", "TODO.md")]
    paths.append(ROOT / "Tests/README.md")
    paths.extend((ROOT / "Docs").glob("*.md"))
    paths.extend((ROOT / ".agents").glob("**/*.md"))
    paths.extend((ROOT / SKILLS_DIR).glob("**/*.md"))
    # Tool-specific skill directories are symlinks to Skills/; check each file once.
    unique: dict[Path, Path] = {}
    for path in sorted(paths, key=lambda item: len(item.parts)):
        unique.setdefault(path.resolve(), path)
    return sorted(
        path
        for path in unique.values()
        if path.is_file() and relative(path) not in LOCAL_ONLY_PATHS
    )


def skill_names() -> set[str]:
    skills_root = ROOT / SKILLS_DIR
    if not skills_root.is_dir():
        return set()
    return {path.name for path in skills_root.iterdir() if (path / "SKILL.md").is_file()}


def check_required_paths(errors: list[str]) -> None:
    for path in REQUIRED_DOCS:
        if not (ROOT / path).exists():
            add_error(errors, f"{path} отсутствует")


def check_references(errors: list[str]) -> None:
    known_skills = skill_names()
    known_prefixes = {name.split("-", 1)[0] for name in known_skills}
    for path in governed_markdown_paths():
        source = relative(path)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            location = f"{source}:{line_number}"
            for match in REPOSITORY_PATH_PATTERN.finditer(line):
                if not (ROOT / match.group(2)).is_dir():
                    continue
                target = match.group(1).rstrip(".,:;")
                if PATH_PLACEHOLDER_CHARACTERS & set(target) or target in LOCAL_ONLY_PATHS:
                    continue
                if not (ROOT / target).exists():
                    add_error(errors, f"{location} ссылается на несуществующий путь {target}")
            for match in MARKDOWN_LINK_PATTERN.finditer(line):
                target = match.group(1).split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                if not (path.parent / target).exists():
                    add_error(errors, f"{location} содержит битую ссылку {match.group(1)}")
            for name in SKILL_REFERENCE_PATTERN.findall(line):
                # Only names under an existing skill prefix are references; `$skill-name` in
                # prose is a syntax example.
                if name.split("-", 1)[0] in known_prefixes and name not in known_skills:
                    add_error(errors, f"{location} ссылается на несуществующий skill {name}")


def check_navigation(errors: list[str]) -> None:
    docs_index = read_text("Docs/README.md")
    for path in sorted((ROOT / "Docs").glob("*.md")):
        if path.name != "README.md" and f"](./{path.name})" not in docs_index:
            add_error(errors, f"Docs/README.md не ссылается на {path.name}")
    readme = read_text("README.md")
    for target in (
        "./Docs/README.md",
        "./Tests/README.md",
        "./AGENTS.md",
    ):
        if f"]({target})" not in readme:
            add_error(errors, f"README.md не ссылается на {target}")


def check_backlog_notice(errors: list[str]) -> None:
    if TODO_BACKLOG_MARKER not in read_text("TODO.md"):
        add_error(errors, "TODO.md не предупреждает, что backlog не описывает текущее поведение")


def main() -> int:
    errors: list[str] = []
    check_required_paths(errors)
    if errors:
        print("Docs check failed:")
        print("\n".join(errors))
        return 1
    check_references(errors)
    check_navigation(errors)
    check_backlog_notice(errors)
    if errors:
        print("Docs check failed:")
        print("\n".join(errors))
        return 1
    print("Docs check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
