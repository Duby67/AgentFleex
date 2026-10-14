"""Check the plugin version and changelogs, and print release notes.

`check`: both manifests carry one x.y.z version, `CHANGELOG.md` has `## Unreleased` first at most
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

MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
RELEASE = re.compile(r"## \[(\d+\.\d+\.\d+)\]\(https://\S+/releases/tag/\1\)")


class Fail(Exception):
    """An error with an actionable message."""


def version(root: Path) -> str:
    found = {json.loads((root / path).read_text(encoding="utf-8"))["version"] for path in MANIFESTS}
    if len(found) != 1:
        raise Fail(f"plugin.json versions differ: {', '.join(sorted(found))}; set one version")
    value = found.pop()
    if not SEMVER.fullmatch(value):
        raise Fail(f"plugin.json version {value!r} is not x.y.z")
    return value


def changelogs(root: Path) -> list[Path]:
    return [root / "CHANGELOG.md", *sorted(root.glob("docs/*/CHANGELOG.md"))]


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
    english = list(sections(root / "CHANGELOG.md"))
    for i, head in enumerate(english):
        if not (head == "## Unreleased" and i == 0 or RELEASE.fullmatch(head)):
            raise Fail(
                f"CHANGELOG.md: unexpected heading {head!r}; use ## Unreleased first, "
                "then ## [x.y.z](<link to the x.y.z release tag>)"
            )
    if not any(head.startswith(f"## [{value}]") for head in english):
        raise Fail(f"CHANGELOG.md: add a ## [{value}] section for the manifest version")
    for path in changelogs(root):
        found = sections(path)
        name = path.relative_to(root).as_posix()
        if list(found) != english:
            raise Fail(f"{name}: headings must match CHANGELOG.md")
        if release and found.get("## Unreleased", "").strip():
            raise Fail(f"{name}: move the ## Unreleased items to ## [{value}]")
        if release and not section(found, value).strip():
            raise Fail(f"{name}: no notes under ## [{value}]")
    if release:
        tags = subprocess.run(
            ["git", "tag", "--list"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.split()
        if value in tags:
            raise Fail(f"tag {value} already exists; raise the version in both plugin.json files")
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
    sub.add_parser("notes", help="print the release notes of the manifest version")
    args = parser.parse_args()
    root = Path.cwd()
    try:
        if args.command == "check":
            print(check(root, args.release))
        else:
            sys.stdout.write(notes(root))
    except Fail as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
