(project)=

# Project

Development happens in a single [uv] workspace: one lockfile, one virtual
environment, two publishable packages under `packages/`.

## Set up

```console
$ uv sync --all-packages --group dev
```

This installs both workspace packages editable plus the docs, testing, and
lint tooling.

## Development loop

Run every change through this loop:

```console
$ uv run ruff format .
```

```console
$ uv run pytest
```

```console
$ uv run ruff check . --fix --show-fixes
```

```console
$ uv run ty check
```

The [just] recipes wrap these: `just test`, `just ruff`, `just ruff-format`,
`just ty`, and `just build-docs`.

```{toctree}
:hidden:

contributing
releasing
```

[uv]: https://docs.astral.sh/uv/
[just]: https://just.systems/
