"""Synchronize plugin manifest versions with the root VERSION file.

VERSION must be greater than every release tag before anything is checked or written.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")
RELEASE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def parse(version: str) -> tuple[int, ...] | None:
    match = RELEASE.fullmatch(version)
    return tuple(int(part) for part in match.groups()) if match else None


def read_version(root: Path) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if parse(version) is None:
        raise ValueError("VERSION: expected a release version such as 0.3.1")
    return version


def require_bump(version: str, tags: list[str]) -> None:
    """Fail unless version is greater than every tag that is a release version."""
    current = parse(version)
    if current is None:
        raise ValueError(f"VERSION: {version} is not a release version such as 0.3.1")
    released = [(parsed, tag) for tag in tags if (parsed := parse(tag)) is not None]
    if released and current <= max(released)[0]:
        raise ValueError(
            f"VERSION: {version} must be greater than the latest release tag "
            f"{max(released)[1]}; bump VERSION and run python .github/scripts/version.py"
        )


def git_tags(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "tag", "--list"],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"git tag --list failed: {result.stderr.strip()}")
    return result.stdout.split()


def sync(root: Path, *, check: bool) -> None:
    version = read_version(root)
    updates = []
    for name in MANIFESTS:
        path = root / name
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("version"), str):
            raise ValueError(f"{name}: expected a JSON object with a string version")
        if manifest["version"] != version:
            manifest["version"] = version
            updates.append((path, manifest))
    if check and updates:
        names = ", ".join(str(path.relative_to(root)) for path, _ in updates)
        raise ValueError(
            f"{names}: version differs from VERSION; run python .github/scripts/version.py"
        )
    for path, manifest in updates:
        path.write_bytes(
            (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check without changing manifests")
    args = parser.parse_args()
    try:
        require_bump(read_version(ROOT), git_tags(ROOT))
        sync(ROOT, check=args.check)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
