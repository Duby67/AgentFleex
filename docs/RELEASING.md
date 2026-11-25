# Releasing AgentFleex

Versions follow [Semantic Versioning](https://semver.org/). While the version is `0.x`, the minor
number marks changed or removed behavior of skills and hooks, and the patch number marks fixes and
additions. Installed plugins update only when the version is raised. `develop` has no version of
its own; it carries the last released one until a release raises it.

## Preparing a release

A request to prepare a release or a release PR authorizes a version bump. If the need for a
bump comes from your own assessment, ask the user before changing the version.

Every merge into `main` is a release:

1. On `develop`, raise `project.version` in `pyproject.toml` above the latest tag, then run
   `uv lock` and the sync command to update both plugin manifests:

   ```bash
   uv run --locked python skills/fleex-repo/scripts/release.py \
     --manifest .claude-plugin/plugin.json --manifest .codex-plugin/plugin.json sync
   ```

2. Rename `## Unreleased` to `## [x.y.z](https://github.com/Duby67/AgentFleex/releases/tag/x.y.z)`
   in the changelog and leave an empty `## Unreleased` above it.
3. Run the local checks and push `develop`.
4. Open a pull request from `develop` into `main`. The release check verifies the source branch,
   manifest versions, an empty `## Unreleased`, notes for the new version, and a version above the
   latest tag. [Release script](../skills/fleex-repo/scripts/release.py)
5. Merge with **Create a merge commit**. Squash and rebase merges rewrite the commits, so `main` and
   `develop` diverge.
6. The push to `main` repeats the release check, tags the version, and publishes it as the latest
   GitHub release with the notes from that section.

A bug in a release is fixed on `develop` and shipped with the next patch version.
