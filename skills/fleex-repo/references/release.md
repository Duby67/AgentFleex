# Releases

Every merge into `main` is a release; CI tags it and publishes a GitHub release with notes from the
changelog. There are no release or hotfix branches: the release source branch (`develop`, or
`staging`) holds only finished changes, and a bug in a release ships with the next patch version.

## Versions

- Semantic Versioning `x.y.z`. While the major number is `0`, the minor marks changed or removed
  behavior, and the patch marks fixes and additions.
- One version source, the first present of `pyproject.toml` (`project.version`), `package.json`
  (`version`), and a one-line `VERSION` file. Other JSON files that repeat the version are
  manifests kept in sync by the script.
- The release source branch has no version of its own; it carries the last released one until a
  release raises it.

## Changelog

`docs/CHANGELOG.md` starts with `## Unreleased`, then one
`## [x.y.z](https://github.com/<owner>/<repo>/releases/tag/x.y.z)` section per release, newest
first, each a short list of solved problems and resulting behavior. Translations at
`docs/<code>/CHANGELOG.md` have the same headings and notes for every release.

## Mechanism

Copy `../scripts/release.py` to `.github/scripts/release.py`; it needs Python 3.11+ (or `tomli`) and
`git`. Pass each manifest as `--manifest <file>` before the command.

- `release.py sync` copies the version to the manifests.
- A local pre-commit hook runs `release.py check` when the version source, a manifest, or a
  changelog changes: manifests match, the headings are valid, and the version has a section.
- The `version` job in CI runs `release.py check --release` on a pull request into `main`: the
  source branch is the release source, `## Unreleased` is empty, every changelog has notes, and the
  version is above the latest tag and untagged.
- The `release` job repeats that check on the push to `main`, then tags the version and publishes
  the release with `release.py notes`.

## Making a release

1. On the release source branch, raise the version above the latest tag, run `release.py sync`
   and the lockfile update, rename `## Unreleased` to the version in every changelog, and leave an
   empty `## Unreleased` above it.
2. Push, open a pull request into `main`, and merge it with a merge commit once the checks pass.
   Squash and rebase merges rewrite commits, so `main` and the source branch would diverge.
