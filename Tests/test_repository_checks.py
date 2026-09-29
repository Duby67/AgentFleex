from collections.abc import Callable
from pathlib import Path

import pytest

from Scripts.check_agent_rules import check_agent_rules
from Scripts.check_docs import check_backlog_notice, check_navigation, check_references


def write(root: Path, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_check(
    check: Callable[[list[str]], None], monkeypatch: pytest.MonkeyPatch, root: Path
) -> list[str]:
    for module in ("check_docs", "check_agent_rules"):
        monkeypatch.setattr(f"Scripts.{module}.ROOT", root)
    errors: list[str] = []
    check(errors)
    return errors


def test_references_report_missing_paths_links_and_skills(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    write(tmp_path, "Skills/demo-known/SKILL.md", "Use `$demo-known`.")
    write(tmp_path, "Skills/kit-known/SKILL.md", "Use `$kit-known`.")
    write(tmp_path, "Scripts/present.py", "")
    write(
        tmp_path,
        "Docs/GUIDE.md",
        "`Scripts/present.py` `Scripts/removed.py` `Config/.env` `Tests/test_<name>.py`\n"
        "[ok](../Scripts/present.py) [gone](./MISSING.md#part) [web](https://example.com)\n"
        "$demo-known $demo-renamed $kit-known $kit-missing $skill-name\n",
    )

    errors = run_check(check_references, monkeypatch, tmp_path)

    assert errors == [
        "- Docs/GUIDE.md:1 ссылается на несуществующий путь Scripts/removed.py",
        "- Docs/GUIDE.md:2 содержит битую ссылку ./MISSING.md#part",
        "- Docs/GUIDE.md:3 ссылается на несуществующий skill demo-renamed",
        "- Docs/GUIDE.md:3 ссылается на несуществующий skill kit-missing",
    ]


def test_navigation_requires_every_canonical_doc_in_index(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    write(tmp_path, "Docs/README.md", "[PRODUCT.md](./PRODUCT.md)")
    write(tmp_path, "Docs/PRODUCT.md", "")
    write(tmp_path, "Docs/RUNBOOK.md", "")
    write(
        tmp_path,
        "README.md",
        "[d](./Docs/README.md) [t](./Tests/README.md) [a](./AGENTS.md)",
    )

    errors = run_check(check_navigation, monkeypatch, tmp_path)

    assert errors == ["- Docs/README.md не ссылается на RUNBOOK.md"]


@pytest.mark.parametrize("journal_exists", [False, True])
def test_references_ignore_local_session_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, journal_exists: bool
) -> None:
    write(tmp_path, "AGENTS.md", "Journal: `.agents/handoff.md`.\n")
    write(tmp_path, "Scripts/present.py", "")
    if journal_exists:
        write(tmp_path, ".agents/handoff.md", "Draft: `Scripts/missing.py`.\n")
    write(tmp_path, "Docs/GUIDE.md", "Check: `Scripts/also_missing.py`.\n")

    assert run_check(check_references, monkeypatch, tmp_path) == [
        "- Docs/GUIDE.md:1 ссылается на несуществующий путь Scripts/also_missing.py"
    ]


def test_agent_rules_require_routes_and_english(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    write(tmp_path, "Skills/demo-routed/SKILL.md", "")
    write(tmp_path, "Skills/demo-orphan/SKILL.md", "")
    write(tmp_path, "AGENTS.md", "`Skills/demo-routed/SKILL.md` Пример")

    errors = run_check(check_agent_rules, monkeypatch, tmp_path)

    assert errors == [
        "- AGENTS.md содержит кириллицу; agent-only инструкции должны быть на английском",
        "- AGENTS.md не маршрутизирует skill Skills/demo-orphan/SKILL.md",
    ]


def test_backlog_requires_notice(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    write(tmp_path, "TODO.md", "# TODO")

    assert run_check(check_backlog_notice, monkeypatch, tmp_path) == [
        "- TODO.md не предупреждает, что backlog не описывает текущее поведение"
    ]


def test_references_check_only_paths_under_top_level_directories(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # `src/...` is checked only once the project has a top-level src/ directory.
    write(tmp_path, "Docs/GUIDE.md", "`src/app.py` `Docs/missing.md` `owner/name`\n")

    assert run_check(check_references, monkeypatch, tmp_path) == [
        "- Docs/GUIDE.md:1 ссылается на несуществующий путь Docs/missing.md"
    ]
