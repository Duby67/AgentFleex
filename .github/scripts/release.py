"""Check the plugin version and changelogs, and print release notes.

`sync`: copy project.version from pyproject.toml to both manifests.
`check`: both manifests match project.version, `docs/CHANGELOG.md` has `## Unreleased` first at most
and then `## [x.y.z](<link to the x.y.z release tag>)` sections, the version has a section, and
every translation has the same headings. `check --release` also requires an empty `## Unreleased`,
notes for the version in every changelog, and a version above every x.y.z tag with no tag of its
own. `notes`: the English section, then each translation's section collapsed under its language.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
RELEASE = re.compile(r"## \[(\d+\.\d+\.\d+)\]\(https://\S+/releases/tag/\1\)")


class Fail(Exception):
    """An error with an actionable message."""


def version(root: Path) -> str:
    try:
        project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        value = project["project"]["version"]
    except (OSError, ValueError, KeyError) as error:
        raise Fail(f"pyproject.toml: set project.version to x.y.z ({error})") from error
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise Fail(f"pyproject.toml project.version {value!r} is not x.y.z")
    return value


def manifests(root: Path, value: str, sync: bool = False) -> None:
    for path in MANIFESTS:
        file = root / path
        found = json.loads(file.read_text(encoding="utf-8"))
        if found.get("version") == value:
            continue
        if not sync:
            raise Fail(
                f"{path}: version differs from pyproject.toml ({value}); "
                "run uv run --locked python .github/scripts/release.py sync"
            )
        found["version"] = value
        file.write_text(json.dumps(found, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


ENGLISH = "docs/CHANGELOG.md"


def changelogs(root: Path) -> list[Path]:
    return [root / ENGLISH, *sorted(root.glob("docs/*/CHANGELOG.md"))]


def sections(path: Path) -> dict[str, str]:
    """Headings in order, each with the text under it."""
    found: dict[str, str] = {}
    head = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            head = line
            found[head] = ""
        elif head:
            found[head] += line + "\n"
    return found


def check(root: Path, release: bool) -> str:
    value = version(root)
    manifests(root, value)
    english = list(sections(root / ENGLISH))
    for i, head in enumerate(english):
        if not (head == "## Unreleased" and i == 0 or RELEASE.fullmatch(head)):
            raise Fail(
                f"{ENGLISH}: unexpected heading {head!r}; use ## Unreleased first, "
                "then ## [x.y.z](<link to the x.y.z release tag>)"
            )
    if not any(head.startswith(f"## [{value}]") for head in english):
        raise Fail(f"{ENGLISH}: add a ## [{value}] section for the manifest version")
    for path in changelogs(root):
        found = sections(path)
        name = path.relative_to(root).as_posix()
        if list(found) != english:
            raise Fail(f"{name}: headings must match {ENGLISH}")
        if release and found.get("## Unreleased", "").strip():
            raise Fail(f"{name}: move the ## Unreleased items to ## [{value}]")
        if release and not section(found, value).strip():
            raise Fail(f"{name}: no notes under ## [{value}]")
    if release:
        tags = subprocess.run(
            ["git", "tag", "--list"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.split()
        if value in tags:
            raise Fail(f"tag {value} already exists; raise project.version and sync the manifests")
        older = [tag for tag in tags if SEMVER.fullmatch(tag)]
        latest = max(older, key=key, default=None)
        if latest and key(value) <= key(latest):
            raise Fail(f"version {value} is not above the latest tag {latest}; raise it")
    return value


def key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def section(found: dict[str, str], value: str) -> str:
    return next((text for head, text in found.items() if head.startswith(f"## [{value}]")), "")


def notes(root: Path) -> str:
    value = version(root)
    english, *translations = changelogs(root)
    text = section(sections(english), value).strip() + "\n"
    for path in translations:
        # The bold current language in the switcher line names the translation.
        match = re.search(r"\*\*([^*]+)\*\*", path.read_text(encoding="utf-8"))
        if not match:
            raise Fail(f"{path}: no bold language name in its switcher line")
        body = section(sections(path), value).strip()
        text += f"\n<details><summary>{match.group(1)}</summary>\n\n{body}\n\n</details>\n"
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("check", help="check the version and changelogs")
    run.add_argument("--release", action="store_true", help="also require a releasable version")
    sub.add_parser("sync", help="copy project.version to both manifests")
    sub.add_parser("notes", help="print the release notes of project.version")
    args = parser.parse_args()
    root = Path.cwd()
    try:
        if args.command == "check":
            print(check(root, args.release))
        elif args.command == "sync":
            value = version(root)
            manifests(root, value, sync=True)
            print(value)
        else:
            sys.stdout.buffer.write(notes(root).encode("utf-8"))
    except Fail as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
