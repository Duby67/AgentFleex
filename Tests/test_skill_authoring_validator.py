from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "Scripts" / "check_skills.py"


def make_skill(
    root: Path,
    *,
    directory_name: str = "demo-skill",
    frontmatter_name: str = "demo-skill",
    body: str = "# Demo Skill\n\nRun the focused workflow.",
    description: str = (
        "Validate a demo skill. Use when testing validation. Do not use for runtime work."
    ),
    short_description: str = "Проверяет тестовый проектный скилл",
    default_prompt: str | None = None,
    allow_implicit_invocation: bool | None = None,
    create_openai_yaml: bool = True,
    openai_yaml: str | None = None,
) -> Path:
    skill_dir = root / directory_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {frontmatter_name}\ndescription: {description}\n---\n\n{body}\n",
        encoding="utf-8",
    )
    if create_openai_yaml:
        agents_dir = skill_dir / "agents"
        agents_dir.mkdir()
        if openai_yaml is None:
            prompt = default_prompt or (
                f"Используй ${frontmatter_name} для проверки тестового скилла."
            )
            openai_yaml = (
                "interface:\n"
                '  display_name: "Demo Skill"\n'
                f'  short_description: "{short_description}"\n'
                f'  default_prompt: "{prompt}"\n'
            )
            if allow_implicit_invocation is not None:
                value = str(allow_implicit_invocation).lower()
                openai_yaml += f"\npolicy:\n  allow_implicit_invocation: {value}\n"
        (agents_dir / "openai.yaml").write_text(openai_yaml, encoding="utf-8")
    return skill_dir


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_repository_skills_are_valid() -> None:
    result = run_validator(ROOT / ".agents" / "skills")

    assert result.returncode == 0, result.stdout


def test_accepts_english_instructions_and_russian_ui_metadata(tmp_path: Path) -> None:
    result = run_validator(make_skill(tmp_path))

    assert result.returncode == 0, result.stdout
    assert "PASS" in result.stdout


def test_rejects_missing_openai_yaml(tmp_path: Path) -> None:
    result = run_validator(make_skill(tmp_path, create_openai_yaml=False))

    assert result.returncode == 1
    assert "agents/openai.yaml is required" in result.stdout


def test_rejects_name_directory_mismatch(tmp_path: Path) -> None:
    result = run_validator(make_skill(tmp_path, directory_name="wrong-name"))

    assert result.returncode == 1
    assert "must match skill name 'demo-skill'" in result.stdout


def test_rejects_missing_negative_trigger(tmp_path: Path) -> None:
    result = run_validator(
        make_skill(tmp_path, description="Validate a demo skill. Use when testing validation.")
    )

    assert result.returncode == 1
    assert "negative or exclusive trigger boundary" in result.stdout


def test_rejects_duplicate_frontmatter_name(tmp_path: Path) -> None:
    make_skill(tmp_path, directory_name="first-skill", frontmatter_name="shared-skill")
    make_skill(tmp_path, directory_name="second-skill", frontmatter_name="shared-skill")

    result = run_validator(tmp_path)

    assert result.returncode == 1
    assert "Duplicate frontmatter name 'shared-skill'" in result.stdout


def test_rejects_broken_relative_reference(tmp_path: Path) -> None:
    result = run_validator(
        make_skill(tmp_path, body="# Demo Skill\n\nRead [details](references/missing.md).")
    )

    assert result.returncode == 1
    assert "references a missing file" in result.stdout


def test_rejects_absolute_private_path(tmp_path: Path) -> None:
    result = run_validator(
        make_skill(tmp_path, body="# Demo Skill\n\nRead C:\\Users\\alice\\secret.txt.")
    )

    assert result.returncode == 1
    assert "contains an absolute private path" in result.stdout


def test_rejects_human_only_html_comment(tmp_path: Path) -> None:
    result = run_validator(
        make_skill(tmp_path, body="# Demo Skill\n\n<!-- Maintainer reminder. -->")
    )

    assert result.returncode == 1
    assert "forbidden human-only commentary" in result.stdout


def test_rejects_oversized_skill(tmp_path: Path) -> None:
    oversized_body = "# Demo Skill\n\n" + "\n".join("Run step." for _ in range(201))
    result = run_validator(make_skill(tmp_path, body=oversized_body))

    assert result.returncode == 1
    assert "exceeds the project limit of 200 lines" in result.stdout


def test_rejects_invalid_openai_yaml(tmp_path: Path) -> None:
    result = run_validator(make_skill(tmp_path, openai_yaml="interface: [broken"))

    assert result.returncode == 1
    assert "agents/openai.yaml contains invalid YAML" in result.stdout


def test_rejects_duplicate_frontmatter_key(tmp_path: Path) -> None:
    skill_dir = make_skill(tmp_path)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: demo-skill\n"
        "name: duplicate-skill\n"
        "description: Validate a demo skill. Use when testing. Do not use for runtime.\n"
        "---\n\n# Demo Skill\n",
        encoding="utf-8",
    )

    result = run_validator(skill_dir)

    assert result.returncode == 1
    assert "found duplicate key 'name'" in result.stdout


def test_rejects_cyrillic_in_agent_only_instructions(tmp_path: Path) -> None:
    result = run_validator(make_skill(tmp_path, body="# Demo Skill\n\nЗапусти workflow."))

    assert result.returncode == 1
    assert "agent-only skill content must be English" in result.stdout


def test_rejects_english_user_facing_ui_text(tmp_path: Path) -> None:
    result = run_validator(
        make_skill(
            tmp_path,
            short_description="Validate a project skill package",
            default_prompt="Use $demo-skill to validate this skill.",
        )
    )

    assert result.returncode == 1
    assert "short_description must be user-facing Russian text" in result.stdout
    assert "default_prompt must be user-facing Russian text" in result.stdout


def test_explicit_skill_requires_implicit_invocation_to_be_disabled(tmp_path: Path) -> None:
    result = run_validator(
        make_skill(
            tmp_path,
            description=(
                "Prepare a gated phase. Use only when the user explicitly invokes this phase. "
                "Do not use for ordinary work."
            ),
        )
    )

    assert result.returncode == 1
    assert "policy.allow_implicit_invocation to false" in result.stdout


def test_explicit_skill_accepts_disabled_implicit_invocation(tmp_path: Path) -> None:
    result = run_validator(
        make_skill(
            tmp_path,
            description=(
                "Prepare a gated phase. Use only when the user explicitly invokes this phase. "
                "Do not use for ordinary work."
            ),
            allow_implicit_invocation=False,
        )
    )

    assert result.returncode == 0, result.stdout


def test_shared_kit_skill_uses_english_metadata(tmp_path: Path) -> None:
    skill = make_skill(
        tmp_path,
        directory_name="kit-example",
        frontmatter_name="kit-example",
        short_description="Navigate architecture and direct test imports",
        default_prompt="Use $kit-example to find architectural context.",
    )
    assert run_validator(skill).returncode == 0
    metadata = skill / "agents/openai.yaml"
    metadata.write_text(
        metadata.read_text().replace(
            "Navigate architecture and direct test imports",
            "Поиск архитектуры и прямых импортов тестов",
        )
    )
    result = run_validator(skill)
    assert result.returncode == 1
    assert "must be English for kit skills" in result.stdout
