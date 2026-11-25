# GitHub

Templates are in `../assets/github/`. Obtain the repository name and visibility with
`gh repo view --json nameWithOwner,visibility`.

## Files

- Use issue and PR templates in public or private projects where they help. Adapt the skeletons
  to the project's workflows and keep only fields maintainers use. Add a private reporting link
  only when its destination exists. Templates take effect on the default branch.
- When Dependabot is explicitly requested, adapt `dependabot.yml` to the ecosystems and manifest
  locations the repository uses. Schedule one monthly minor/patch group per ecosystem. Keep
  major versions and security fixes in individual PRs. Leave grouped security updates disabled.
  Dependabot uses the default branch for security updates. Set `target-branch` only to send
  version updates to a different branch.
- Adapt `workflows/ci.yml` to the existing CI, branch names, pre-commit setup, and test commands.
  For projects without releases, omit the version and release jobs and their triggers.
- Use the optional `assets/docs/` skeletons only under the conditions in the repository skill.
  Fill them with the project's actual contribution workflow or security reporting policy.

## CI conventions

- Pin every action to a full commit SHA with its version as a comment.
- Top-level `permissions: contents: read`; grant write only to the job that needs it.
- Run CI pre-commit before expensive builds and tests on pull requests into the working branch,
  and require the result before merging.
- Use separate post-merge workflows for security or release tasks that need the merged state.
- Checkouts that do not push set `persist-credentials: false`; every job has `timeout-minutes`.

## Staging

With `staging`, set `RELEASE_FROM: staging` and keep staging deployment in its own workflow.

## Settings

Show each command and run it only after the user confirms. Read the state first, for example
`gh api repos/<owner>/<repo>`.

- If the agreed default branch is `develop`: `gh repo edit --default-branch develop`.
- For the squash-to-develop and merge-to-main workflow:
  `gh repo edit --enable-squash-merge --enable-merge-commit
  --enable-rebase-merge=false --delete-branch-on-merge`.
- For public projects with a requested vulnerability reporting workflow:
  `gh api -X PUT repos/<owner>/<repo>/private-vulnerability-reporting`.
