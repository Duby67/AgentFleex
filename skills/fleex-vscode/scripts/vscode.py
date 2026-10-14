"""Set up a VS Code profile from this plugin's extension packs and settings.

Standard library only. `apply` installs the packs' VSIX files into the profile, creating the profile
when it is missing, and merges the packs' settings into its settings.json. VSIX files come from
--vsix or are downloaded from the GitHub release of the plugin version (the only network access).
Under WSL the Windows VS Code is configured, since only it manages profiles.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parent.parent
PACKS = SKILL / "assets/packs"
PROFILES = SKILL / "assets/profiles.json"
PLUGIN = SKILL.parent.parent / ".claude-plugin/plugin.json"
DEFAULT = "Default"
WAIT = 60


class Fail(Exception):
    """An error with an actionable message for the user."""


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Fail(f"{path}: not found") from None
    except json.JSONDecodeError as error:
        raise Fail(
            f"{path}: not plain JSON ({error}); remove comments and trailing commas, "
            "or merge the settings by hand"
        ) from None


def profiles() -> dict[str, list[str]]:
    data: dict[str, list[str]] = read_json(PROFILES)
    return data


def packs() -> list[str]:
    return sorted(path.parent.name for path in PACKS.glob("*/package.json"))


def wsl() -> bool:
    return sys.platform == "linux" and "microsoft" in platform.release().lower()


def winpath(path: Path) -> str:
    run = subprocess.run(["wslpath", "-w", str(path)], capture_output=True, text=True, check=True)
    return run.stdout.strip()


def find_code(given: str | None) -> str:
    if given:
        return given
    if wsl():
        # The remote CLI of a WSL window cannot manage profiles; use the Windows launcher.
        for entry in os.environ.get("PATH", "").split(os.pathsep):
            if entry.startswith("/mnt/") and (Path(entry) / "code").is_file():
                return str(Path(entry) / "code")
        raise Fail("Windows VS Code CLI not found on PATH; pass --code /mnt/c/.../bin/code")
    found = shutil.which("code")
    if not found:
        raise Fail("VS Code CLI 'code' not found on PATH; pass --code <path>")
    return found


def find_user_dir(given: str | None) -> Path:
    if given:
        return Path(given)
    if wsl():
        run = subprocess.run(
            ["cmd.exe", "/c", "echo %APPDATA%"],
            capture_output=True,
            text=True,
            cwd="/mnt/c",
            check=False,
        )
        appdata = run.stdout.strip()
        if run.returncode or not appdata or "%" in appdata:
            raise Fail("cannot read Windows %APPDATA%; pass --user-dir <VS Code User directory>")
        args = ["wslpath", "-u", appdata]
        unix = subprocess.run(args, capture_output=True, text=True, check=True)
        return Path(unix.stdout.strip()) / "Code/User"
    if sys.platform == "win32":
        return Path(os.environ["APPDATA"]) / "Code/User"
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Code/User"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "Code/User"


def profile_dir(user: Path, name: str) -> Path | None:
    if name == DEFAULT:
        return user
    storage = user / "globalStorage/storage.json"
    if not storage.is_file():
        return None
    for entry in read_json(storage).get("userDataProfiles") or []:
        if entry.get("name") == name:
            location = entry.get("location")
            if not isinstance(location, str):
                raise Fail(f"{storage}: unknown location format of profile {name!r}: {location!r}")
            return user / "profiles" / location
    return None


def ensure_profile(code: str, user: Path, name: str) -> Path:
    found = profile_dir(user, name)
    if found:
        return found
    # The CLI installs only into an existing profile; opening a window with it creates it.
    subprocess.run([code, "--profile", name, "--new-window"], check=True)
    deadline = time.monotonic() + WAIT
    while time.monotonic() < deadline:
        found = profile_dir(user, name)
        if found:
            return found
        time.sleep(1)
    raise Fail(f"profile {name!r} did not appear in {user} within {WAIT}s; create it in VS Code")


def vsix_files(names: list[str], given: str | None, temp: Path) -> list[Path]:
    if given:
        files = []
        for name in names:
            matches = sorted(Path(given).glob(f"fleex-pack-{name}-*.vsix"))
            if len(matches) != 1:
                raise Fail(f"{given}: expected one fleex-pack-{name}-*.vsix, found {len(matches)}")
            files.append(matches[0])
        return files
    plugin = read_json(PLUGIN)
    version, repository = plugin["version"], plugin["repository"].rstrip("/")
    files = []
    for name in names:
        file = f"fleex-pack-{name}-{version}.vsix"
        url = f"{repository}/releases/download/{version}/{file}"
        try:
            urllib.request.urlretrieve(url, temp / file)
        except urllib.error.URLError as error:
            raise Fail(
                f"{url}: {error}; update the plugin to a release with packs, "
                "or build them with 'npx @vscode/vsce package' and pass --vsix"
            ) from None
        files.append(temp / file)
    return files


def merged_settings(target: Path, names: list[str]) -> dict[str, Any]:
    settings: dict[str, Any] = read_json(target) if target.is_file() else {}
    for name in names:
        settings.update(read_json(PACKS / name / "settings.json"))
    return settings


def apply(args: argparse.Namespace) -> None:
    known = profiles()
    if args.profile not in known and not args.add:
        raise Fail(f"unknown profile {args.profile!r}; known: {', '.join(known)}; or pass --add")
    names = list(dict.fromkeys(known.get(args.profile, []) + (args.add or [])))
    unknown = sorted(set(names) - set(packs()))
    if unknown:
        raise Fail(f"unknown packs {', '.join(unknown)}; known: {', '.join(packs())}")
    code, user = find_code(args.code), find_user_dir(args.user_dir)
    # An unreadable settings.json of an existing profile fails before anything is installed.
    found = profile_dir(user, args.profile)
    if found:
        merged_settings(found / "settings.json", names)
    target = (found or ensure_profile(code, user, args.profile)) / "settings.json"
    flags = [] if args.profile == DEFAULT else ["--profile", args.profile]
    with tempfile.TemporaryDirectory() as temp:
        for vsix in vsix_files(names, args.vsix, Path(temp)):
            path = winpath(vsix) if wsl() and code.startswith("/mnt/") else str(vsix)
            subprocess.run([code, "--install-extension", path, "--force", *flags], check=True)
    settings = merged_settings(target, names)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(settings, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.profile}: installed packs {', '.join(names)}; settings merged into {target}")
    if args.open:
        subprocess.run([code, *flags, args.open], check=True)


def show() -> None:
    for name in packs():
        manifest = read_json(PACKS / name / "package.json")
        size = len(manifest["extensionPack"])
        print(f"pack {name}: {manifest['description']} ({size} extensions)")
    for profile, names in profiles().items():
        print(f"profile {profile}: {', '.join(names)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="packs with their purpose, and the packs of each profile")
    run = sub.add_parser("apply", help="install a profile's packs and merge their settings")
    run.add_argument("profile", help=f"profile name from profiles.json; {DEFAULT} is VS Code's own")
    run.add_argument("--add", nargs="+", metavar="PACK", help="extra packs for this profile")
    run.add_argument("--vsix", metavar="DIR", help="local fleex-pack-*.vsix instead of downloads")
    run.add_argument("--code", help="VS Code CLI to use")
    run.add_argument("--user-dir", help="VS Code User directory")
    run.add_argument("--open", metavar="DIR", help="then open DIR with the profile")
    args = parser.parse_args()
    try:
        if args.command == "list":
            show()
        else:
            apply(args)
    except Fail as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"error: {' '.join(error.cmd)} exited with {error.returncode}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
