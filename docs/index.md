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

:::{grid-item-card} {octicon}`download` Install
:link: install
:link-type: doc
Add the core package or the admin integration to a Django project.
:::

:::{grid-item-card} {octicon}`package` Packages
:link: packages/index
:link-type: doc
The core query language and the optional admin integration.
:::

:::{grid-item-card} {octicon}`book` Reference
:link: packages/django-search-query/reference
:link-type: doc
The public API: parse, build_q, search_query_to_q, the field registry.
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
behavior, so an application gets a consistent search syntax without committing
to a particular user interface, admin integration, or search backend. Its
scope is intentionally loose: the syntax is Lucene-inspired without claiming
full Lucene compatibility.

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
install
packages/index
project/index
history
GitHub <https://github.com/tony/django-search-query>
```
