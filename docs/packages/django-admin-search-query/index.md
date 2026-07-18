(django-admin-search-query)=

# django-admin-search-query

An optional Django admin integration built on top of
{doc}`django-search-query <../django-search-query/index>`.

It adds structured search support to Django admin changelist pages while
keeping the underlying query language usable independently. The relationship
between the two packages stays loose so the core package never couples to
Django admin behavior or presentation concerns.

## Optional JavaScript input

The package may also provide an optional, self-contained search input
implemented in vanilla JavaScript. The input could offer:

- syntax highlighting of the query as it is typed,
- contextual suggestions for fields and operators, and
- semantic autocomplete for field values.

It is designed to degrade gracefully: when JavaScript is unavailable or
disabled, the input remains usable as a normal text field.

```{note}
This package is early scaffolding. The admin mixin and the JavaScript input
are not implemented yet; this page describes the intended scope.
```

## Install

Installing the admin integration pulls in the core query language:

```console
$ pip install django-admin-search-query
```

```console
$ uv add django-admin-search-query
```
