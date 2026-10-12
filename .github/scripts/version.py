"""Synchronize plugin manifest versions with the root VERSION file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json")


def sync(root: Path, *, check: bool) -> None:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", version):
        raise ValueError("VERSION: expected a release version such as 0.3.1")
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
        sync(ROOT, check=args.check)
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
