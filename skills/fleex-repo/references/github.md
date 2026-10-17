# GitHub

Templates are in `../assets/github/`; `<owner>/<repo>` comes from `gh repo view --json
nameWithOwner`.

## Files

- `ISSUE_TEMPLATE/`: bug and feature forms, and `config.yml` that disables blank issues and links
  private vulnerability reports. Copy to `.github/ISSUE_TEMPLATE/`; adapt the form fields to the
  project (the versions a bug report needs, a client or platform dropdown).
- `pull_request_template.md`: copy to `.github/`. Templates take effect once they reach the default
  branch.
- `dependabot.yml`: copy to `.github/`; it updates the pinned action SHAs. Add an entry for each
  package ecosystem the repository uses (`uv`, `pip`, `npm`, `docker`). Give every entry
  `target-branch: develop`, also with `staging`: without it Dependabot targets `main`, and CI
  rejects that pull request.
- `workflows/ci.yml`: copy to `.github/workflows/` when the repository has no CI, or merge its jobs
  into the existing workflow. Fill the test command or delete that step. Without releases, drop
  the `version` and `release` jobs and the `pull_request` trigger.
- `../assets/docs/SECURITY.md` and `../assets/docs/CONTRIBUTING.md`: skeletons for `docs/`; their
  text follows $fleex-docs.

## CI conventions

- Pin every action to a full commit SHA with its version as a comment; Dependabot keeps them
  current.
- Top-level `permissions: contents: read`; grant write only to the job that needs it.
- Run the hygiene checks through pre-commit and the project's tests on pushes to `develop`; a pull
  request into `main` shows those results for its head commit.

## Staging

With `staging`, `develop` merges into `staging` and `staging` into `main`. In `ci.yml`, add
`staging` to the push branches, set `RELEASE_FROM: staging`, and add the project's deployment to
the test server as a job on pushes to `staging`.

## Settings

Show each command and run it only after the user confirms. Read the state first, for example
`gh api repos/<owner>/<repo>`.

- Default branch `main`: `gh repo edit --default-branch main`.
- Merge commits allowed, branches deleted after merge:
  `gh repo edit --enable-merge-commit --delete-branch-on-merge`.
- Private vulnerability reporting:
  `gh api -X PUT repos/<owner>/<repo>/private-vulnerability-reporting`.
