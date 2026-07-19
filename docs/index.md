(index)=

# django-search-query

A reusable, [Lucene]-inspired search query language for [Django] -- and an
optional [Django admin] integration built on top of it.

::::{grid} 1 1 2 3
:gutter: 2 2 3 3

:::{grid-item-card} {octicon}`rocket` Tutorial
:link: tutorial
:link-type: doc
Build a search registry and run a query against a Django queryset.
:::

:::{grid-item-card} {octicon}`search` Query language
:link: query
:link-type: doc
The search syntax, and the magic: a query string becomes a Q object and filters a queryset.
:::

:::{grid-item-card} {octicon}`download` Install
:link: install
:link-type: doc
Add the core package or the admin integration to a Django project.
:::

:::{grid-item-card} {octicon}`book` API reference
:link: api
:link-type: doc
search_query_to_q, parse, build_q, the field registry, and the admin mixin.
:::

:::{grid-item-card} {octicon}`package` Packages
:link: packages/index
:link-type: doc
The core query language and the optional admin integration.
:::

:::{grid-item-card} {octicon}`tools` Project
:link: project/index
:link-type: doc
Development setup, contributing, and the release process.
:::

:::{grid-item-card} {octicon}`log` Changelog
:link: history
:link-type: doc
Per-package release notes.
:::

::::

## Install

```console
$ pip install django-search-query
```

```console
$ uv add django-search-query
```

The admin integration installs separately; see {doc}`install`.

## What this is

{doc}`django-search-query <packages/django-search-query/index>` accepts a
structured search string and translates it into Django-compatible query
behavior, so an application gets a consistent {doc}`search syntax <query>`
without committing to a particular user interface, admin integration, or
search backend. Under the hood that string becomes a
{class}`~django.db.models.Q` you hand to any
{class}`~django.db.models.query.QuerySet` -- see {doc}`query` for the syntax and the
worked query-to-queryset examples. Its scope is intentionally loose: the
syntax is Lucene-inspired without claiming full Lucene compatibility.

{doc}`django-admin-search-query <packages/django-admin-search-query/index>`
is an optional add-on that brings that same structured search to Django admin
changelist pages while keeping the core language usable on its own -- the
relationship stays loose so the core package never couples to admin behavior
or presentation concerns. It also optionally ships a self-contained,
vanilla-JavaScript search input with syntax highlighting, contextual
suggestions, and semantic autocomplete that degrades to a plain text field
when JavaScript is unavailable.

[Lucene]: https://lucene.apache.org/
[Django]: https://docs.djangoproject.com/
[Django admin]: https://docs.djangoproject.com/en/stable/ref/contrib/admin/

```{toctree}
:hidden:

tutorial
query
install
api
packages/index
project/index
history
GitHub <https://github.com/tony/django-search-query>
```
