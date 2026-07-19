(django-admin-search-query)=

# django-admin-search-query

An optional Django admin integration built on top of
{doc}`django-search-query <../django-search-query/index>`.

It adds structured search support to Django admin changelist pages while
keeping the underlying query language usable independently. The relationship
between the two packages stays loose so the core package never couples to
Django admin behavior or presentation concerns.

## Colored search input

`SearchQueryAdminMixin` also ships an optional, self-contained search input
implemented in vanilla JavaScript. The highlighting is computed **on the
server** -- there is no JavaScript tokenizer -- so the colors can never drift
from the Python engine. The input offers:

- syntax highlighting of the query as it is typed, including a registry-aware
  `error` role for unknown fields and out-of-enum values,
- keyboard-navigable autocomplete for field names and enum values, and
- graceful degradation: with JavaScript unavailable or offline, the box stays a
  plain text field that still submits `?q=`.

See {doc}`colored-input` for the endpoint contract and the design.

## Install

Installing the admin integration pulls in the core query language:

```console
$ pip install django-admin-search-query
```

```console
$ uv add django-admin-search-query
```

```{toctree}
:hidden:

colored-input
```
