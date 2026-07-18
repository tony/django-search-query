(contributing)=

# Contributing

## Workspace layout

```text
packages/
  django-search-query/          # core query language
    src/django_search_query/
  django-admin-search-query/    # optional admin integration
    src/django_admin_search_query/
tests/                          # shared test suite (settings, smoke tests)
docs/                           # this documentation site
```

All shared tooling -- ruff, ty, pytest, coverage -- is configured once in the
root `pyproject.toml` and applies to every package.

## Standards

- Every Python file starts with `from __future__ import annotations`.
- NumPy-style docstrings; ruff enforces `pydocstyle`.
- Type hints are required and checked with [ty].
- Public functions and methods carry working doctests once they exist.

See `AGENTS.md` at the repository root for the full contributor guide.

[ty]: https://docs.astral.sh/ty/
