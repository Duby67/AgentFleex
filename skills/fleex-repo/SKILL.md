---
name: fleex-repo
description: User-invoked audit and setup of a GitHub repository's service files and settings: README, LICENSE, .gitignore, .gitattributes, SECURITY, CONTRIBUTING, issue and PR templates, Dependabot, CI, and the version, changelog, and release mechanism. Use only when the user asks to audit, set up, or align a repository with their conventions, or to set up releases. Do not use for AGENTS.md, skills, or docs content alone.
disable-model-invocation: true
---

# Repository

Apply shared organization principles to the repository's actual needs and existing conventions.
GitHub only.

## Audit

Report each item as present, missing, or differing from the conventions below; never change files
during an audit. Findings may go to the backlog as $fleex-docs describes.

- Assess existing files against the project's needs. Report missing files only when they support
  a requested workflow or a tool the project already uses.
- Keep the project's license choice. A private project may have no license file.
- Consider `SECURITY.md` only for public repositories when the request covers public maintenance
  or vulnerability reporting. Consider `CONTRIBUTING.md` only for projects with multiple
  contributors when the request covers collaboration. These requests need not name the files.
- Configure Dependabot only when the user explicitly asks for Dependabot.
- Conventions: actions pinned by full commit SHA with a version comment, top-level
  `permissions: contents: read`, the branch model of `AGENTS.md`, and only the release source
  branch merging into `main`.

## Owners

Each area has one owner; follow it instead of repeating it here:

- `AGENTS.md`, `.claude/CLAUDE.md`, and branch rules: $fleex-agents.
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
- Keep established branches. For a new GitHub workflow, use the working and release branches
  agreed with the user.
- GitHub files and settings: [the GitHub guide](references/github.md). Versions, changelog, and
  releases: [the release guide](references/release.md); skip them for a repository with no
  releases.
- Changing GitHub settings is outward-facing: run each `gh` command that changes them only after
  the user confirms it.

## Check

From the repository root, run `../fleex-skills/scripts/check.sh` relative to this skill's directory
(`check.ps1` on Windows), run the repository's pre-commit on the new files, and read the changed
GitHub settings back with `gh`.
