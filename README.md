# django-search-query

A reusable, [Lucene]-inspired search query language for [Django], plus an
optional Django admin integration built on top of it. This repository is a
[uv] workspace containing two independently-installable packages.

## Packages

| Package | Description |
| --- | --- |
| [`django-search-query`](packages/django-search-query) | Core query language: parses a structured search string and compiles it to Django ORM lookups. No UI, admin, or backend assumptions. |
| [`django-admin-search-query`](packages/django-admin-search-query) | Optional Django admin integration, plus an optional vanilla-JavaScript search input. Depends on the core package through a loose version floor. |

## Status

Early scaffolding. The query language and admin integration are not
implemented yet; the package skeletons, metadata, and documentation describe
the intended scope. See the [documentation](https://django-search-query.git-pull.com)
for details.

## Development

```console
$ uv sync --all-packages --group dev
```

```console
$ uv run pytest
```

See `AGENTS.md` for the full contributor guide.

## Supported versions

- Python 3.12+
- Django 5.2 (LTS) and 6.0

[Lucene]: https://lucene.apache.org/
[Django]: https://docs.djangoproject.com/
[uv]: https://docs.astral.sh/uv/
