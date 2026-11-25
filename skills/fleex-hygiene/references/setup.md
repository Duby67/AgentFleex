# Setting up style tooling

Apply a setup only after the user agrees to it. Reformatting a whole repository is a separate change.

## Python environment

For Python tooling, including a repository with only Python tests, default to a non-packaged uv
project (`[tool.uv] package = false`) unless it builds a Python distribution. Keep dependencies in
`pyproject.toml`, commit `uv.lock`, ignore `.venv/`, and create it with `uv sync`. Add development
tools with `uv add --dev`; run tests and tools with `uv run --locked`. Preserve an established
environment manager unless the user requests migration.

## pre-commit

For projects adopting pre-commit, start with their existing config or the basic file checks in
`../assets/pre-commit-config.yaml`. Add project-specific checks when they catch meaningful issues
the existing checks miss. Keep hooks fast, pin revisions, and avoid checking the same rule twice.
Contributors install the hook once with
`uv run --locked pre-commit install` in a uv project or `uvx pre-commit install` otherwise.

## Defaults and .editorconfig

Use the project's existing settings. When adding a tool, adapt a relevant config from
`../assets/` if it fits, and keep it in the project's own config where possible. When adding
`.editorconfig`, adapt `../assets/editorconfig` to the formatter's line length and the line
endings in `.gitattributes`. CI and `.editorconfig` must agree with the tool configuration.
