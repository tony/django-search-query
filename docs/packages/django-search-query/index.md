(django-search-query)=

# django-search-query

A reusable query-language package for Django applications.

It accepts structured search input and translates it into Django-compatible
query behavior. The goal is a consistent search syntax that does not require a
particular user interface, admin integration, or search backend.

## Scope

The scope is intentionally loose. The syntax is inspired by [Lucene] --
field-scoped terms (`status:open`), quoted phrases (`"exact match"`), boolean
operators (`AND` / `OR` / `NOT`), and grouping -- but the package does not
claim full Lucene compatibility or identical semantics.

## Intended pipeline

The package is expected to flow a raw search string through a parse pipeline
and compile the result into Django lookups:

```text
Search string
    -> Tokenizer (lexing)
        -> Parser (AST: terms, phrases, boolean / grouped nodes)
            -> Query builder (AST -> Django Q objects / queryset)
```

Callers control which fields are searchable through a field map and
validation hooks, keeping user-facing field names decoupled from ORM lookups.

```{note}
This package is early scaffolding. The tokenizer, parser, AST, and query
builder are not implemented yet; this page describes the intended design.
```

## Install

```console
$ pip install django-search-query
```

```console
$ uv add django-search-query
```

[Lucene]: https://lucene.apache.org/
