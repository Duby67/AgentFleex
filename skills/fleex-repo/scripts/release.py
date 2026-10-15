"""Check the release version and changelogs, and print release notes.

The version source is the first of pyproject.toml (`project.version`), package.json (`version`),
and VERSION (one line). Each `--manifest` is a JSON file whose `version` must match it. The English
changelog is docs/CHANGELOG.md, or CHANGELOG.md without it; translations are
docs/<code>/CHANGELOG.md.

`sync`: copy the version to every manifest.
`check`: every manifest matches the version, the English changelog has `## Unreleased` first at
most and then `## [x.y.z](<link to the x.y.z release tag>)` sections, the version has a section,
and every translation has the same headings. `check --release` also requires an empty
`## Unreleased`, notes for the version in every changelog, and a version above every x.y.z tag
with no tag of its own. `notes`: the English section, then each translation's section collapsed
under its language.
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

SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
RELEASE = re.compile(r"## \[(\d+\.\d+\.\d+)\]\(https://\S+/releases/tag/\1\)")
# Version sources in order of preference, each with the field that holds the version.
SOURCES = {"pyproject.toml": "project.version", "package.json": "version", "VERSION": "the line"}


class Fail(Exception):
    """An error with an actionable message."""


def version(root: Path) -> tuple[str, str]:
    """The version and the file it comes from."""
    source = next((name for name in SOURCES if (root / name).is_file()), None)
    if source is None:
        raise Fail(
            "no version source; add project.version to pyproject.toml, version to package.json, "
            "or a VERSION file"
        )
    text = (root / source).read_text(encoding="utf-8")
    try:
        if source == "pyproject.toml":
            value = tomllib.loads(text)["project"]["version"]
        elif source == "package.json":
            value = json.loads(text)["version"]
        else:
            value = text.strip()
    except (ValueError, KeyError, TypeError) as error:
        raise Fail(f"{source}: set {SOURCES[source]} to x.y.z ({error})") from error
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise Fail(f"{source}: {SOURCES[source]} {value!r} is not x.y.z")
    return value, source


def manifests(root: Path, paths: list[str], value: str, source: str, sync: bool = False) -> None:
    for path in paths:
        file = root / path
        try:
            found = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise Fail(f"{path}: not a readable JSON manifest ({error})") from error
        if found.get("version") == value:
            continue
        if not sync:
            raise Fail(
                f"{path}: version differs from {source} ({value}); "
                "run release.py sync with the same --manifest options"
            )
        found["version"] = value
        file.write_text(json.dumps(found, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def changelogs(root: Path) -> list[Path]:
    english = root / "docs/CHANGELOG.md"
    if not english.is_file():
        english = root / "CHANGELOG.md"
    if not english.is_file():
        raise Fail("no changelog; add docs/CHANGELOG.md with ## Unreleased")
    return [english, *sorted(root.glob("docs/*/CHANGELOG.md"))]


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


def check(root: Path, paths: list[str], release: bool) -> str:
    value, source = version(root)
    manifests(root, paths, value, source)
    files = changelogs(root)
    english_path = files[0]
    english_name = english_path.relative_to(root).as_posix()
    english = list(sections(english_path))
    for i, head in enumerate(english):
        if not (head == "## Unreleased" and i == 0 or RELEASE.fullmatch(head)):
            raise Fail(
                f"{english_name}: unexpected heading {head!r}; use ## Unreleased first, "
                "then ## [x.y.z](<link to the x.y.z release tag>)"
            )
    if not any(head.startswith(f"## [{value}]") for head in english):
        raise Fail(f"{english_name}: add a ## [{value}] section for the version in {source}")
    for path in files:
        found = sections(path)
        name = path.relative_to(root).as_posix()
        if list(found) != english:
            raise Fail(f"{name}: headings must match {english_name}")
        if release and found.get("## Unreleased", "").strip():
            raise Fail(f"{name}: move the ## Unreleased items to ## [{value}]")
        if release and not section(found, value).strip():
            raise Fail(f"{name}: no notes under ## [{value}]")
    if release:
        tags = subprocess.run(
            ["git", "tag", "--list"], cwd=root, capture_output=True, text=True, check=True
        ).stdout.split()
        if value in tags:
            raise Fail(f"tag {value} already exists; raise the version in {source}")
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
    value, _ = version(root)
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
    parser.add_argument(
        "--manifest", action="append", default=[], help="JSON file whose version must match"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("check", help="check the version and changelogs")
    run.add_argument("--release", action="store_true", help="also require a releasable version")
    sub.add_parser("sync", help="copy the version to every manifest")
    sub.add_parser("notes", help="print the release notes of the version")
    args = parser.parse_args()
    root = Path.cwd()
    try:
        if args.command == "check":
            print(check(root, args.manifest, args.release))
        elif args.command == "sync":
            value, source = version(root)
            manifests(root, args.manifest, value, source, sync=True)
            print(value)
        else:
            sys.stdout.buffer.write(notes(root).encode("utf-8"))
    except Fail as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
