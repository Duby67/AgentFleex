# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Validate repository skill packages shared by Codex and Claude Code."""

from __future__ import annotations

import argparse
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CYRILLIC_PATTERN = re.compile(r"[\u0400-\u04FF]")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
EXPLICIT_TRIGGER_PATTERN = re.compile(
    r"\b(?:explicitly (?:label|invoke|designate|request)\w*|explicit invocation)\b",
    re.IGNORECASE,
)
USE_TRIGGER_PATTERN = re.compile(r"\bUse (?:only )?(?:when|for|to)\b")
NEGATIVE_TRIGGER_PATTERN = re.compile(r"\b(?:Do not use|Only use)\b")
PRIVATE_PATH_PATTERNS = (
    re.compile(r"/Users/[^/\s]+/"),
    re.compile(r"/home/[^/\s]+/"),
    re.compile(r"[A-Za-z]:[\\/]Users[\\/][^\\/\s]+[\\/]", re.IGNORECASE),
)
TEXT_SUFFIXES = {
    ".json",
    ".js",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}
FORBIDDEN_HUMAN_MARKERS = (
    "<!--",
    "## For humans",
    "## Human notes",
    "## Maintainer notes",
    "## Reviewer notes",
    "TODO for human",
)
OPENAI_REQUIRED_FIELDS = ("display_name", "short_description", "default_prompt")
MAX_SKILL_LINES = 200
MAX_SKILL_CHARACTERS = 20_000


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def load_yaml_mapping(text: str, label: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = yaml.load(text, Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        return None, f"{label} contains invalid YAML: {exc}"
    if not isinstance(value, Mapping):
        return None, f"{label} must contain a YAML mapping."
    if not all(isinstance(key, str) for key in value):
        return None, f"{label} mapping keys must be strings."
    return dict(value), None


def read_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if len(lines) < 4 or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter.")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("SKILL.md frontmatter is not closed with '---'.") from exc

    metadata, error = load_yaml_mapping("\n".join(lines[1:end]), "SKILL.md frontmatter")
    if error:
        raise ValueError(error)
    assert metadata is not None
    return metadata, "\n".join(lines[end + 1 :])


def validate_relative_links(skill_dir: Path, text: str, errors: list[str]) -> None:
    for target in MARKDOWN_LINK_PATTERN.findall(text):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean_target = target.split("#", 1)[0]
        if not clean_target:
            continue
        target_path = Path(clean_target)
        if target_path.is_absolute():
            errors.append(f"SKILL.md contains an absolute Markdown link: {target}")
            continue
        if len(target_path.parts) > 2:
            errors.append(f"Skill references must remain one level deep: {target}")
        if not (skill_dir / target_path).exists():
            errors.append(f"SKILL.md references a missing file: {target}")


def validate_text_files(skill_dir: Path, errors: list[str]) -> None:
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(skill_dir).as_posix()

        if relative != "agents/openai.yaml" and CYRILLIC_PATTERN.search(text):
            errors.append(
                f"{relative} contains Cyrillic text; agent-only skill content must be English."
            )
        for marker in FORBIDDEN_HUMAN_MARKERS:
            if marker.lower() in text.lower():
                errors.append(f"{relative} contains forbidden human-only commentary: {marker}")
        for pattern in PRIVATE_PATH_PATTERNS:
            if pattern.search(text):
                errors.append(f"{relative} contains an absolute private path.")


def validate_openai_yaml(
    skill_dir: Path,
    name: str,
    description: str,
    errors: list[str],
) -> None:
    relative = "agents/openai.yaml"
    path = skill_dir / relative
    if not path.exists():
        errors.append(f"{relative} is required for repo-scoped skills.")
        return

    metadata, error = load_yaml_mapping(path.read_text(encoding="utf-8"), relative)
    if error:
        errors.append(error)
        return
    assert metadata is not None

    interface = metadata.get("interface")
    if not isinstance(interface, Mapping):
        errors.append(f'{relative} must contain an "interface" mapping.')
        return

    for field in OPENAI_REQUIRED_FIELDS:
        if not isinstance(interface.get(field), str) or not interface[field].strip():
            errors.append(f'{relative} must contain non-empty interface field "{field}".')

    short_description = interface.get("short_description")
    if isinstance(short_description, str):
        if not 25 <= len(short_description) <= 64:
            errors.append(f"{relative} short_description must contain 25-64 characters.")
        if name.startswith("kit-") and CYRILLIC_PATTERN.search(short_description):
            errors.append(f"{relative} short_description must be English for kit skills.")
        elif not name.startswith("kit-") and not CYRILLIC_PATTERN.search(short_description):
            errors.append(f"{relative} short_description must be user-facing Russian text.")

    default_prompt = interface.get("default_prompt")
    if isinstance(default_prompt, str):
        if name.startswith("kit-") and CYRILLIC_PATTERN.search(default_prompt):
            errors.append(f"{relative} default_prompt must be English for kit skills.")
        elif not name.startswith("kit-") and not CYRILLIC_PATTERN.search(default_prompt):
            errors.append(f"{relative} default_prompt must be user-facing Russian text.")
        if name and f"${name}" not in default_prompt:
            errors.append(f"{relative} default_prompt must mention ${name}.")

    policy = metadata.get("policy", {})
    if not isinstance(policy, Mapping):
        errors.append(f'{relative} field "policy" must be a mapping.')
        return
    allow_implicit = policy.get("allow_implicit_invocation")
    if allow_implicit is not None and not isinstance(allow_implicit, bool):
        errors.append(f"{relative} policy.allow_implicit_invocation must be a boolean.")
    if EXPLICIT_TRIGGER_PATTERN.search(description) and allow_implicit is not False:
        errors.append(
            f"{relative} must set policy.allow_implicit_invocation to false "
            "for an explicitly invoked skill."
        )


def validate_skill(skill_dir: Path) -> tuple[str, list[str]]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return "", ["SKILL.md is missing."]

    text = skill_file.read_text(encoding="utf-8")
    try:
        metadata, body = read_frontmatter(text)
    except ValueError as exc:
        return "", [str(exc)]

    name_value = metadata.get("name")
    description_value = metadata.get("description")
    name = name_value if isinstance(name_value, str) else ""
    description = description_value if isinstance(description_value, str) else ""

    if not name:
        errors.append("Frontmatter field 'name' must be a non-empty string.")
    elif len(name) > 64:
        errors.append("Frontmatter field 'name' must be at most 64 characters.")
    elif not NAME_PATTERN.fullmatch(name):
        errors.append(
            "Frontmatter field 'name' must use lowercase letters, numbers, and single hyphens."
        )
    if name and skill_dir.name != name:
        errors.append(f"Directory name '{skill_dir.name}' must match skill name '{name}'.")

    if not description:
        errors.append("Frontmatter field 'description' must be a non-empty string.")
    elif len(description) > 1024:
        errors.append("Frontmatter field 'description' must be at most 1024 characters.")
    if description and not USE_TRIGGER_PATTERN.search(description):
        errors.append("Description must state when to use the skill.")
    if description and not NEGATIVE_TRIGGER_PATTERN.search(description):
        errors.append("Description must state a negative or exclusive trigger boundary.")

    if len(text.splitlines()) > MAX_SKILL_LINES:
        errors.append(f"SKILL.md exceeds the project limit of {MAX_SKILL_LINES} lines.")
    if len(text) > MAX_SKILL_CHARACTERS:
        errors.append(f"SKILL.md exceeds the project limit of {MAX_SKILL_CHARACTERS:,} characters.")
    if not body.strip():
        errors.append("SKILL.md body must not be empty.")

    validate_relative_links(skill_dir, text, errors)
    validate_text_files(skill_dir, errors)
    validate_openai_yaml(skill_dir, name, description, errors)
    return name, errors


def collect_skill_dirs(paths: list[Path]) -> tuple[list[Path], list[str]]:
    result: list[Path] = []
    errors: list[str] = []
    for path in paths:
        if path.is_file() and path.name == "SKILL.md":
            result.append(path.parent)
        elif path.is_dir() and (path / "SKILL.md").exists():
            result.append(path)
        elif path.is_dir():
            discovered = sorted(item.parent for item in path.rglob("SKILL.md"))
            if not discovered:
                errors.append(f"{path} does not contain any skills.")
            result.extend(discovered)
        else:
            errors.append(f"{path} does not exist or is not a skill path.")
    return list(dict.fromkeys(item.resolve() for item in result)), errors


def validate_paths(paths: list[Path]) -> tuple[dict[Path, list[str]], list[str]]:
    skill_dirs, discovery_errors = collect_skill_dirs(paths)
    results: dict[Path, list[str]] = {}
    names: dict[str, list[Path]] = {}

    for skill_dir in skill_dirs:
        name, errors = validate_skill(skill_dir)
        results[skill_dir] = errors
        if name:
            names.setdefault(name, []).append(skill_dir)

    for name, duplicate_dirs in names.items():
        if len(duplicate_dirs) < 2:
            continue
        rendered = ", ".join(str(path) for path in duplicate_dirs)
        for skill_dir in duplicate_dirs:
            results[skill_dir].append(f"Duplicate frontmatter name '{name}' found in: {rendered}")

    return results, discovery_errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    results, discovery_errors = validate_paths(args.paths)
    failed = bool(discovery_errors)
    for error in discovery_errors:
        print(f"FAIL {error}")

    for skill_dir, errors in results.items():
        if errors:
            failed = True
            print(f"FAIL {skill_dir}")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"PASS {skill_dir}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
