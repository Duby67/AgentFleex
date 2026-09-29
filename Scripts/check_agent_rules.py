"""Check that AGENTS.md stays English and routes every repository skill."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILLS_DIR = "Skills"
CYRILLIC_PATTERN = re.compile(r"[Ѐ-ӿ]")


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def add_error(errors: list[str], message: str) -> None:
    errors.append(f"- {message}")


def skill_names() -> set[str]:
    skills_root = ROOT / SKILLS_DIR
    if not skills_root.is_dir():
        return set()
    return {path.name for path in skills_root.iterdir() if (path / "SKILL.md").is_file()}


def check_agent_rules(errors: list[str]) -> None:
    agents_text = read_text("AGENTS.md")
    if CYRILLIC_PATTERN.search(agents_text):
        add_error(
            errors, "AGENTS.md содержит кириллицу; agent-only инструкции должны быть на английском"
        )
    for name in sorted(skill_names()):
        route = f"{SKILLS_DIR}/{name}/SKILL.md"
        if route not in agents_text:
            add_error(errors, f"AGENTS.md не маршрутизирует skill {route}")


def main() -> int:
    errors: list[str] = []
    check_agent_rules(errors)
    if errors:
        print("Agent rules check failed:")
        print("\n".join(errors))
        return 1
    print("Agent rules check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
