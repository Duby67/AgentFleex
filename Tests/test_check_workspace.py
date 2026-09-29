from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from Scripts import check_workspace


def completed(
    arguments: list[str], returncode: int = 0, stdout: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(arguments, returncode, stdout=stdout, stderr="")


def git_responses(
    root: Path,
    *,
    origin: str = "https://github.com/example/project.git",
    branch: str = "qol-bootstrap-check",
    worktree: str = "",
    counts: str = "0 2",
    ancestor_code: int = 0,
    base_ref: str = "origin/integration",
) -> dict[tuple[str, ...], subprocess.CompletedProcess[str]]:
    return {
        ("rev-parse", "--show-toplevel"): completed([], stdout=str(root)),
        ("remote", "get-url", "origin"): completed([], stdout=origin),
        ("status", "--porcelain=v1", "--untracked-files=all"): completed([], stdout=worktree),
        ("branch", "--show-current"): completed([], stdout=branch),
        ("rev-parse", "--verify", base_ref): completed([], stdout="base-sha"),
        ("rev-list", "--left-right", "--count", f"{base_ref}...HEAD"): completed([], stdout=counts),
        ("merge-base", "--is-ancestor", base_ref, "HEAD"): completed([], returncode=ancestor_code),
        ("log", "--oneline", "--decorate", f"{base_ref}..HEAD"): completed(
            [], stdout="abc123 Task commit"
        ),
        ("diff", "--name-status", f"{base_ref}...HEAD"): completed(
            [], stdout="M\tScripts/check_workspace.py"
        ),
    }


def install_fake_git(
    monkeypatch: pytest.MonkeyPatch,
    responses: dict[tuple[str, ...], subprocess.CompletedProcess[str]],
) -> None:
    def fake_run(arguments: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        assert arguments[0] == "git"
        return responses[tuple(arguments[1:])]

    monkeypatch.setattr(check_workspace.subprocess, "run", fake_run)


@pytest.mark.parametrize(
    ("remote", "expected"),
    (
        ("https://token@github.com/example/project.git", "example/project"),
        ("git@github.com:example/project.git", "example/project"),
        ("ssh://git@github.com/example/project.git", "example/project"),
    ),
)
def test_repository_slug_redacts_transport_and_credentials(remote: str, expected: str) -> None:
    assert check_workspace.repository_slug(remote) == expected


def test_clean_dedicated_branch_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_git(monkeypatch, git_responses(tmp_path))

    report = check_workspace.inspect_workspace(
        tmp_path,
        expected_repository="example/project",
        base_ref="origin/integration",
        fetch=False,
    )

    assert report.errors == ()
    assert report.ahead == 2
    assert report.behind == 0


def test_dirty_worktree_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_git(monkeypatch, git_responses(tmp_path, worktree=" M AGENTS.md"))

    report = check_workspace.inspect_workspace(
        tmp_path,
        expected_repository="example/project",
        base_ref="origin/integration",
        fetch=False,
    )

    assert "Working tree contains tracked or untracked changes." in report.errors


@pytest.mark.parametrize("branch", ("integration", "dev", "production"))
def test_protected_branch_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    branch: str,
) -> None:
    install_fake_git(monkeypatch, git_responses(tmp_path, branch=branch))

    report = check_workspace.inspect_workspace(
        tmp_path,
        expected_repository="example/project",
        base_ref="origin/integration",
        fetch=False,
    )

    assert f"Branch '{branch}' is protected; use a dedicated task branch." in report.errors


def test_base_must_be_an_ancestor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_git(monkeypatch, git_responses(tmp_path, ancestor_code=1))

    report = check_workspace.inspect_workspace(
        tmp_path,
        expected_repository="example/project",
        base_ref="origin/integration",
        fetch=False,
    )

    assert (
        "origin/integration is not an ancestor of HEAD; rebase requires explicit approval."
        in report.errors
    )


def test_mismatched_origin_never_exposes_raw_url(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    secret_url = "https://super-secret@github.com/other/repository.git"
    install_fake_git(monkeypatch, git_responses(tmp_path, origin=secret_url))
    report = check_workspace.inspect_workspace(
        tmp_path,
        expected_repository="example/project",
        base_ref="origin/integration",
        fetch=False,
    )

    check_workspace.print_report(report)
    output = capsys.readouterr().out

    assert "super-secret" not in output
    assert "origin must point to example/project" in output


def start_responses(
    root: Path,
    *,
    branch: str = "integration",
    worktree: str = "",
    upstream: tuple[int, str] = (0, "origin/integration"),
    unpublished: str = "0",
) -> dict[tuple[str, ...], subprocess.CompletedProcess[str]]:
    upstream_code, upstream_ref = upstream
    published_refs = (
        (upstream_ref, "origin/integration") if upstream_ref else ("origin/integration",)
    )
    return {
        ("rev-parse", "--show-toplevel"): completed([], stdout=str(root)),
        ("remote", "get-url", "origin"): completed(
            [], stdout="https://github.com/example/project.git"
        ),
        ("status", "--porcelain=v1", "--untracked-files=all"): completed([], stdout=worktree),
        ("rev-parse", "--verify", "origin/integration"): completed([], stdout="base-sha"),
        ("branch", "--show-current"): completed([], stdout=branch),
        ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"): completed(
            [], returncode=upstream_code, stdout=upstream_ref
        ),
        ("rev-list", "--count", "HEAD", "--not", *published_refs): completed(
            [], stdout=unpublished
        ),
    }


def inspect_start(root: Path) -> check_workspace.StartReport:
    return check_workspace.inspect_start(
        root,
        expected_repository="example/project",
        base_ref="origin/integration",
        fetch=False,
    )


@pytest.mark.parametrize(
    ("branch", "upstream"),
    (
        ("integration", (0, "origin/integration")),
        ("fix-merged-task", (128, "")),
    ),
)
def test_start_accepts_clean_published_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    branch: str,
    upstream: tuple[int, str],
) -> None:
    install_fake_git(monkeypatch, start_responses(tmp_path, branch=branch, upstream=upstream))

    assert inspect_start(tmp_path).errors == ()


@pytest.mark.parametrize(
    ("overrides", "error"),
    (
        ({"worktree": "?? notes.md"}, "Working tree contains tracked or untracked changes."),
        (
            {
                "branch": "feature-draft",
                "upstream": (0, "origin/feature-draft"),
                "unpublished": "2",
            },
            (
                "Branch 'feature-draft' has 2 unpushed commit(s); push it before creating a task "
                "branch."
            ),
        ),
        (
            {"branch": "feature-draft", "upstream": (128, ""), "unpublished": "1"},
            (
                "Branch 'feature-draft' has no upstream and 1 commit(s) outside "
                "origin/integration; push it before creating a task branch."
            ),
        ),
    ),
)
def test_start_rejects_uncommitted_or_unpushed_work(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, Any],
    error: str,
) -> None:
    install_fake_git(monkeypatch, start_responses(tmp_path, **overrides))

    assert inspect_start(tmp_path).errors == (error,)


def test_platform_detects_native_linux() -> None:
    report = check_workspace.inspect_platform(
        "/home/developer/projects/project",
        require_linux=True,
        platform_name="linux",
        os_release="6.8.0-generic",
        environment={},
    )

    assert report.kind == "native Linux"
    assert report.errors == ()


def test_platform_detects_wsl_and_public_distribution_name() -> None:
    report = check_workspace.inspect_platform(
        "/home/developer/projects/project",
        require_linux=True,
        platform_name="linux",
        os_release="5.15.153.1-microsoft-standard-WSL2",
        environment={"WSL_DISTRO_NAME": "Ubuntu-24.04"},
    )

    assert report.kind == "WSL"
    assert report.distribution == "Ubuntu-24.04"


def test_platform_detects_native_windows() -> None:
    report = check_workspace.inspect_platform(
        r"C:\projects\project",
        require_linux=False,
        platform_name="win32",
        environment={},
    )

    assert report.kind == "native Windows"
    assert "does not cover Linux-only checks" in report.warnings[0]


def test_wsl_repository_under_home_is_recommended() -> None:
    report = check_workspace.inspect_platform(
        "/home/developer/projects/project",
        require_linux=False,
        platform_name="linux",
        os_release="microsoft-standard-WSL2",
        environment={"WSL_DISTRO_NAME": "Ubuntu"},
    )

    assert report.warnings == ()


def test_wsl_repository_under_windows_mount_warns() -> None:
    report = check_workspace.inspect_platform(
        "/mnt/c/projects/project",
        require_linux=False,
        platform_name="linux",
        os_release="microsoft-standard-WSL2",
        environment={"WSL_DISTRO_NAME": "Ubuntu"},
    )

    assert "/mnt/<drive>" in report.warnings[0]


def test_require_linux_rejects_native_windows() -> None:
    report = check_workspace.inspect_platform(
        r"C:\projects\project",
        require_linux=True,
        platform_name="win32",
        environment={},
    )

    assert report.errors == (
        "--require-linux requires native Linux or WSL; native Windows is not enough.",
    )


def test_require_linux_cli_exits_with_error_on_native_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    install_fake_git(monkeypatch, git_responses(tmp_path))
    monkeypatch.setattr(check_workspace.sys, "platform", "win32")
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_workspace.py", "--repo", str(tmp_path), "--require-linux"],
    )

    assert check_workspace.main() == 1
    output = capsys.readouterr().out
    assert "Platform: native Windows" in output
    assert "Platform errors:" in output


def test_origin_is_not_checked_without_expected_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_fake_git(
        monkeypatch, git_responses(tmp_path, origin="https://github.com/other/fork.git")
    )
    report = check_workspace.inspect_workspace(
        tmp_path, expected_repository=None, base_ref="origin/integration", fetch=False
    )

    assert report.errors == ()
    assert report.repository == "other/fork"


def test_worktree_status_keeps_the_leading_index_column(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_fake_git(monkeypatch, git_responses(tmp_path, worktree=" M AGENTS.md\n"))
    report = check_workspace.inspect_workspace(
        tmp_path, expected_repository=None, base_ref="origin/integration", fetch=False
    )

    assert report.worktree == (" M AGENTS.md",)
