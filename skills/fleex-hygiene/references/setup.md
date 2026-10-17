# Setting up style tooling

Apply a setup only after the user agrees to it. Reformatting a whole repository is a separate change.

## Python environment

For Python tooling, including a repository with only Python tests, default to a non-packaged uv
project (`[tool.uv] package = false`) unless it builds a Python distribution. Keep dependencies in
`pyproject.toml`, commit `uv.lock`, ignore `.venv/`, and create it with `uv sync`. Add development
tools with `uv add --dev`; run tests and tools with `uv run --locked`. Preserve an established
environment manager unless the user requests migration.

## pre-commit

Every repository runs its hygiene checks through pre-commit. Without `.pre-commit-config.yaml`,
start from `../assets/pre-commit-config.yaml` (whitespace, end of file, merge conflicts, YAML and
JSON syntax, markdownlint, yamllint) and add the repository's existing linters, formatters, and type
checkers; pin every `rev` to a commit with `pre-commit autoupdate --freeze`. Copy
`../assets/markdownlint.yaml` and `../assets/yamllint.yaml` to `.github/linters/.markdownlint.yaml`
and `.github/linters/.yamllint.yaml` unless the repository configures those tools already. CI runs
`pre-commit run --all-files`; contributors install it once with `uv run --locked pre-commit install`
in a uv project, or `uvx pre-commit install` otherwise.

## Defaults and .editorconfig

When asked to add or unify tooling, start from the plugin defaults in `../assets/`: copy their
settings into an existing file (`pyproject.toml`, `package.json`) where possible, so the repository
no longer depends on the plugin. Without `.editorconfig`, copy `../assets/editorconfig` to the root
as `.editorconfig`, with `max_line_length` matching the formatter and line endings matching
`.gitattributes`. CI and `.editorconfig` must agree with the tool configuration.
