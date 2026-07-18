# django-search-query

A reusable query-language package for Django applications.

It accepts structured search input and translates it into Django-compatible
query behavior, providing a consistent search syntax without requiring a
particular user interface, admin integration, or search backend.

The scope is intentionally loose: the syntax is inspired by [Lucene] --
field-scoped terms, quoted phrases, boolean operators, and grouping -- without
claiming full Lucene compatibility or identical semantics.

> [!NOTE]
> Early scaffolding. The tokenizer, parser, AST, and query builder are not
> implemented yet.

## Install

```console
$ pip install django-search-query
```

## Supported versions

- Python 3.12+
- Django 5.2 (LTS) and 6.0

## Documentation

https://django-search-query.git-pull.com

[Lucene]: https://lucene.apache.org/
