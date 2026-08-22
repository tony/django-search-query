# django-search-query

A reusable, [Lucene]-inspired search query language for [Django], plus an
optional Django admin integration built on top of it. This repository is a
[uv] workspace containing two independently-installable packages.

## Packages

| Package | Description |
| --- | --- |
| [`django-search-query`](packages/django-search-query) | Core query language: parses a structured search string and compiles it to Django ORM lookups. No UI, admin, or backend assumptions. |
| [`django-admin-search-query`](packages/django-admin-search-query) | Optional Django admin integration, plus an optional vanilla-JavaScript search input. Depends on the core package through a loose version floor. |

## Install

```console
$ pip install django-search-query
```

```console
$ uv add django-search-query
```

Installing `django-admin-search-query` pulls in the core package
automatically; install it the same way to add the optional admin
integration. Register whichever package you install in `INSTALLED_APPS` --
see the [documentation](https://django-search-query.git-pull.com) for what
the admin integration additionally needs.

## Quickstart

Declare which fields a query string may touch, then compile one:

```python
from django_search_query import search_query_to_q
from django_search_query.registry import FieldRegistry, FieldSpec

registry = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
search_query_to_q(
    "status:open",
    registry=registry,
    field_map={"status": "status"},
    default_fields=("title", "body"),
)
```

This compiles to `<Q: (AND: ('status__iexact', 'open'))>`, which you pass to
`.filter()` like any other `Q`. The same call is checked as a doctest in the
documentation and pinned in `tests/test_query_examples.py`. A query the
parser cannot read raises `QueryParseError`; the admin integration catches it
and falls back to a plain search instead of breaking the changelist.

## Status

> [!WARNING]
> **Alpha.** Releases carry an `-alpha` prerelease tag. The API is not settled,
> and any release may change or remove exported identifiers without a
> deprecation period. Pin an exact version. Not recommended for production.

See the [documentation](https://django-search-query.git-pull.com) for the
full query syntax, the admin integration, and the JavaScript search input.

## Development

```console
$ uv sync --all-packages --group dev
```

```console
$ uv run pytest
```

See [`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) for the full
contributor guide.

## Supported versions

- Python 3.12+
- Django 5.2 (LTS), 6.0, and 6.1

[Lucene]: https://lucene.apache.org/
[Django]: https://docs.djangoproject.com/
[uv]: https://docs.astral.sh/uv/
