---
name: fleex-repo
description: Explicitly invoked setup of new GitHub repositories or audit and refresh of existing repositories against AgentFleex assets and conventions.
disable-model-invocation: true
---

# Repository

Apply shared organization principles to the repository's actual needs and existing conventions.
GitHub only.

## Audit

Audit without changing files or settings. Select the assets relevant to the requested workflows
and compare their behavior with the project's files, CI, and GitHub settings. For each actionable
gap, cite the asset, show the current behavior, and explain what alignment would change.
Respect deliberate project conventions and identify settings you could not verify.

- Assess existing files against the project's needs. Report missing files only when they support
  a requested workflow or a tool the project already uses.
- Keep the project's license choice. A private project may have no license file.
- Consider `SECURITY.md` only for public repositories when the request covers public maintenance
  or vulnerability reporting. Consider `CONTRIBUTING.md` only for projects with multiple
  contributors when the request covers collaboration. These requests need not name the files.
- Configure Dependabot only when the user explicitly asks for Dependabot.
- Conventions: actions pinned by full commit SHA with a version comment, top-level
  `permissions: contents: read`, and the repository's established branch workflow.

## Owners

Each area has one owner; follow it instead of repeating it here:

- `AGENTS.md` and `.claude/CLAUDE.md`: $fleex-agents.
- Project skills and agent skills symlinks: $fleex-skills.
- Text of README, CONTRIBUTING, SECURITY, and the backlog: $fleex-docs.
- Linters, formatters, pre-commit, uv, and `.editorconfig`: $fleex-hygiene.

This skill owns the Git files, the GitHub files and settings, and the release mechanism.

## Layout

The root keeps only files a tool requires there: `README.md`, `LICENSE`, `AGENTS.md`,
`.gitignore`, `.gitattributes`, `.editorconfig`, `.pre-commit-config.yaml`, and package manifests.
Human docs, including `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `TODO.md`, live in
`docs/`; GitHub-only files in `.github/`. Move an existing file only with the user's consent, and
update every link to it in the same change.

## Apply

- Show the plan (files to add or move, settings to change) and apply it after the user agrees.
- Select templates from `assets/` for the agreed workflows. Replace each placeholder with a
  verified project value. Merge with existing files or report differences.
- When refreshing an existing repository, apply the agreed audit findings and preserve
  unrelated configuration and project-specific settings.
- Keep the repository's established conventions. Use this skill's defaults only for workflows
  agreed with the user during repository setup.
- GitHub files and settings: [the GitHub guide](references/github.md). Versions, changelog, and
  releases: [the release guide](references/release.md); skip them for a repository with no
  releases.
- Changing GitHub settings is outward-facing: run each `gh` command that changes them only after
  the user confirms it.

## Check

Run the project's relevant checks on the changed files and read modified GitHub settings back
with `gh`.
