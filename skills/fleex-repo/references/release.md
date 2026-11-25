# Releases

Use the project's established release process. Offer the mechanism below when release setup is
requested and the project has no versioning workflow. Projects without releases can stay unversioned.

Document the adopted process in a dedicated project file and link it from `AGENTS.md` for release
work. A request to prepare a release or release PR can imply a version bump. Ask before bumping
a version on the agent's own initiative. Preparing a release and opening its PR are separate actions.

With this default, merging the release PR into `main` tags the version and publishes the changelog
notes. Fix release bugs on `develop` and ship them with the next patch.

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
first. Record user-visible changes under `## Unreleased` as the problem solved and resulting
behavior.

## Mechanism

Copy `../scripts/release.py` to `.github/scripts/release.py`; it needs Python 3.11+ (or `tomli`) and
`git`. Pass each manifest as `--manifest <file>` before the command.

- `release.py sync` copies the version to the manifests.
- A local pre-commit hook runs `release.py check` when the version source, a manifest, or a
  changelog changes: manifests match, the headings are valid, and the version has a section.
- The `version` job in CI runs `release.py check --release` on a pull request into `main`: the
  source branch is the release source, `## Unreleased` is empty, the version has notes, and the
  version is above the latest tag and untagged.
- The `release` job repeats that check on the push to `main`, then tags the version and publishes
  the release with `release.py notes`.

## Making a release

1. On the release source branch, raise the version above the latest tag, run `release.py sync`
   and the lockfile update, rename `## Unreleased` to the version, and leave an
   empty `## Unreleased` above it.
2. Push, open a pull request into `main`, and merge it with a merge commit once the checks pass.
   Squash and rebase merges rewrite commits, so `main` and the source branch would diverge.
