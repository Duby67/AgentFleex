"""Check that the task workspace is safe to work in or to start a new task branch from."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

BRANCH_PATTERN = re.compile(r"^(?:qol|feature|fix|deploy|docs|test)-[a-z0-9][a-z0-9-]*$")
PROTECTED_BRANCHES = {"integration", "dev", "production"}


class WorkspaceCheckError(RuntimeError):
    """Raised when Git cannot provide workspace evidence safely."""


@dataclass(frozen=True)
class PlatformReport:
    kind: str
    distribution: str | None
    warnings: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class WorkspaceReport:
    root: Path
    repository: str
    branch: str
    base_ref: str
    behind: int
    ahead: int
    worktree: tuple[str, ...]
    commits: tuple[str, ...]
    changed_paths: tuple[str, ...]
    errors: tuple[str, ...]


@dataclass(frozen=True)
class StartReport:
    root: Path
    repository: str
    branch: str
    upstream: str
    unpublished: int
    worktree: tuple[str, ...]
    errors: tuple[str, ...]


def _read_os_release() -> str:
    for path in (Path("/proc/sys/kernel/osrelease"), Path("/proc/version")):
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
    return ""


def _public_distribution_name(environment: Mapping[str, str]) -> str:
    value = environment.get("WSL_DISTRO_NAME", "").strip()
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._+-]{0,63}", value):
        return value
    return "unknown"


def _is_windows_mount(path: Path | str) -> bool:
    normalized = str(path).replace("\\", "/")
    return re.match(r"^/mnt/[a-z](?:/|$)", normalized, flags=re.IGNORECASE) is not None


def inspect_platform(
    repo: Path | str,
    *,
    require_linux: bool,
    platform_name: str | None = None,
    os_release: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> PlatformReport:
    detected_platform = sys.platform if platform_name is None else platform_name
    detected_environment = os.environ if environment is None else environment
    warnings: list[str] = []
    errors: list[str] = []
    distribution: str | None = None

    if detected_platform == "linux":
        release = _read_os_release() if os_release is None else os_release
        is_wsl = "microsoft" in release.casefold() or bool(
            detected_environment.get("WSL_INTEROP") or detected_environment.get("WSL_DISTRO_NAME")
        )
        if is_wsl:
            kind = "WSL"
            distribution = _public_distribution_name(detected_environment)
            if _is_windows_mount(repo):
                warnings.append(
                    "The repository is under /mnt/<drive>; use the WSL Linux filesystem "
                    "(for example ~/projects/<repository>) for the recommended full Linux check."
                )
        else:
            kind = "native Linux"
    elif detected_platform == "win32" or detected_platform.startswith("win"):
        kind = "native Windows"
        warnings.append(
            "Native Windows does not cover Linux-only checks; open the repository explicitly "
            "as a VS Code WSL workspace."
        )
    else:
        kind = f"unsupported ({detected_platform})"
        warnings.append("The full local check contract is supported only on Linux and WSL2.")

    if require_linux and kind == "native Windows":
        errors.append("--require-linux requires native Linux or WSL; native Windows is not enough.")
    elif require_linux and kind != "WSL" and kind != "native Linux":
        errors.append("--require-linux requires native Linux or WSL.")

    return PlatformReport(
        kind=kind,
        distribution=distribution,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def run_git(repo: Path, *arguments: str, allowed_codes: tuple[int, ...] = (0,)) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode not in allowed_codes:
        command = "git " + " ".join(arguments)
        raise WorkspaceCheckError(f"{command} failed with exit code {result.returncode}.")
    # Keep leading spaces: `git status --porcelain` encodes the index state in column one.
    return result.stdout.rstrip("\n")


def repository_slug(remote_url: str) -> str | None:
    value = remote_url.strip()
    if not value:
        return None

    if "://" in value:
        parsed = urlparse(value)
        if not parsed.hostname:
            return None
        path = parsed.path
    else:
        scp_match = re.fullmatch(r"(?:[^@\s]+@)?[^:\s]+:(.+)", value)
        if not scp_match:
            return None
        path = scp_match.group(1)

    slug = path.strip("/")
    slug = slug.removesuffix(".git")
    parts = slug.split("/")
    if len(parts) != 2 or not all(parts):
        return None
    return "/".join(parts)


def inspect_origin_and_worktree(
    repo: Path, expected_repository: str | None
) -> tuple[Path, str | None, tuple[str, ...], list[str]]:
    root = Path(run_git(repo, "rev-parse", "--show-toplevel")).resolve()
    origin = run_git(root, "remote", "get-url", "origin")
    actual_repository = repository_slug(origin)
    errors: list[str] = []

    if expected_repository is not None and (
        actual_repository is None or actual_repository.casefold() != expected_repository.casefold()
    ):
        errors.append(
            f"origin must point to {expected_repository}; the raw remote URL was withheld."
        )

    worktree_text = run_git(root, "status", "--porcelain=v1", "--untracked-files=all")
    worktree = tuple(line for line in worktree_text.splitlines() if line)
    if worktree:
        errors.append("Working tree contains tracked or untracked changes.")
    return root, actual_repository, worktree, errors


def inspect_workspace(
    repo: Path,
    *,
    expected_repository: str | None,
    base_ref: str,
    fetch: bool,
) -> WorkspaceReport:
    root, actual_repository, worktree, errors = inspect_origin_and_worktree(
        repo, expected_repository
    )

    branch = run_git(root, "branch", "--show-current")
    if not branch:
        errors.append("HEAD is detached; use a dedicated task branch.")
    elif branch in PROTECTED_BRANCHES:
        errors.append(f"Branch '{branch}' is protected; use a dedicated task branch.")
    elif not BRANCH_PATTERN.fullmatch(branch):
        errors.append(f"Branch '{branch}' does not match a dedicated task branch.")

    expected_base_ref = "origin/integration"
    if base_ref != expected_base_ref:
        errors.append(f"Branch '{branch}' must use base ref {expected_base_ref}, not {base_ref}.")

    if fetch:
        run_git(root, "fetch", "--prune", "origin")

    run_git(root, "rev-parse", "--verify", base_ref)
    counts = run_git(root, "rev-list", "--left-right", "--count", f"{base_ref}...HEAD")
    try:
        behind_text, ahead_text = counts.split()
        behind, ahead = int(behind_text), int(ahead_text)
    except (ValueError, TypeError) as exc:
        raise WorkspaceCheckError(f"Could not parse divergence from {base_ref}.") from exc

    ancestor_result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base_ref, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if ancestor_result.returncode == 1:
        errors.append(f"{base_ref} is not an ancestor of HEAD; rebase requires explicit approval.")
    elif ancestor_result.returncode != 0:
        raise WorkspaceCheckError(
            f"git merge-base --is-ancestor failed with exit code {ancestor_result.returncode}."
        )

    commits_text = run_git(root, "log", "--oneline", "--decorate", f"{base_ref}..HEAD")
    diff_text = run_git(root, "diff", "--name-status", f"{base_ref}...HEAD")

    return WorkspaceReport(
        root=root,
        repository=actual_repository or "(unrecognized origin)",
        branch=branch or "(detached)",
        base_ref=base_ref,
        behind=behind,
        ahead=ahead,
        worktree=worktree,
        commits=tuple(line for line in commits_text.splitlines() if line),
        changed_paths=tuple(line for line in diff_text.splitlines() if line),
        errors=tuple(errors),
    )


def inspect_start(
    repo: Path,
    *,
    expected_repository: str | None,
    base_ref: str,
    fetch: bool,
) -> StartReport:
    """Check that a new task branch can be created without leaving unpublished work behind."""
    root, actual_repository, worktree, errors = inspect_origin_and_worktree(
        repo, expected_repository
    )
    if fetch:
        run_git(root, "fetch", "--prune", "origin")
    run_git(root, "rev-parse", "--verify", base_ref)

    branch = run_git(root, "branch", "--show-current")
    upstream = ""
    unpublished = 0
    if not branch:
        errors.append("HEAD is detached; switch to a pushed branch before creating a task branch.")
    else:
        # A missing or pruned upstream is acceptable only when origin/integration already
        # contains every local commit, for example after the task branch was merged.
        upstream = run_git(
            root,
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
            allowed_codes=(0, 128),
        )
        published_refs = (upstream, base_ref) if upstream else (base_ref,)
        count = run_git(root, "rev-list", "--count", "HEAD", "--not", *published_refs)
        try:
            unpublished = int(count)
        except ValueError as exc:
            raise WorkspaceCheckError("Could not count unpublished commits.") from exc
        if unpublished and upstream:
            errors.append(
                f"Branch '{branch}' has {unpublished} unpushed commit(s); push it before "
                "creating a task branch."
            )
        elif unpublished:
            errors.append(
                f"Branch '{branch}' has no upstream and {unpublished} commit(s) outside "
                f"{base_ref}; push it before creating a task branch."
            )

    return StartReport(
        root=root,
        repository=actual_repository or "(unrecognized origin)",
        branch=branch or "(detached)",
        upstream=upstream or "(none)",
        unpublished=unpublished,
        worktree=worktree,
        errors=tuple(errors),
    )


def print_section(title: str, lines: tuple[str, ...]) -> None:
    print(f"{title}:")
    if lines:
        for line in lines:
            print(f"  {line}")
    else:
        print("  (none)")


def print_platform_report(report: PlatformReport) -> None:
    print(f"Platform: {report.kind}")
    if report.distribution is not None:
        print(f"WSL distribution: {report.distribution}")
    if report.warnings:
        print_section("Platform warnings", report.warnings)
    if report.errors:
        print_section("Platform errors", report.errors)


def print_report(report: WorkspaceReport) -> None:
    print(f"Repository root: {report.root}")
    print(f"Repository: {report.repository}")
    print(f"Branch: {report.branch}")
    print(f"Base: {report.base_ref}")
    print(f"Divergence: behind={report.behind} ahead={report.ahead}")
    print_section("Worktree changes", report.worktree)
    print_section("Branch commits", report.commits)
    print_section("Changed paths", report.changed_paths)
    if report.errors:
        print_section("Workspace errors", report.errors)
    else:
        print("Git workspace check passed.")


def print_start_report(report: StartReport) -> None:
    print(f"Repository root: {report.root}")
    print(f"Repository: {report.repository}")
    print(f"Branch: {report.branch}")
    print(f"Upstream: {report.upstream}")
    print(f"Unpublished commits: {report.unpublished}")
    print_section("Worktree changes", report.worktree)
    if report.errors:
        print_section("Workspace errors", report.errors)
    else:
        print("Start check passed: a new task branch can be created.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--base-ref", default="origin/integration")
    parser.add_argument(
        "--expected-repository",
        help="owner/name that origin must point to, for example to reject a stray clone",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Run 'git fetch --prune origin' before checking the base ref.",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Check the state before creating a new task branch.",
    )
    parser.add_argument(
        "--require-linux",
        action="store_true",
        help="Fail unless the workspace runs on native Linux or inside WSL.",
    )
    args = parser.parse_args()

    inspector = inspect_start if args.start else inspect_workspace
    try:
        report = inspector(
            args.repo,
            expected_repository=args.expected_repository,
            base_ref=args.base_ref,
            fetch=args.fetch,
        )
    except WorkspaceCheckError as exc:
        print(f"Workspace check failed: {exc}")
        return 1

    platform_report = inspect_platform(report.root, require_linux=args.require_linux)
    print_platform_report(platform_report)
    if isinstance(report, StartReport):
        print_start_report(report)
    else:
        print_report(report)
    return 1 if report.errors or platform_report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
