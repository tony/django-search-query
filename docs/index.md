(index)=

# django-search-query

A reusable, [Lucene]-inspired search query language for [Django] -- and an
optional [Django admin] integration built on top of it.

::::{grid} 1 1 2 2
:gutter: 2 2 3 3

:::{grid-item-card} Quickstart
:link: quickstart
:link-type: doc
Install the packages and see where the project is headed.
:::

:::{grid-item-card} Packages
:link: packages/index
:link-type: doc
The core query language and the admin integration, each independently
installable.
:::

:::{grid-item-card} Project
:link: project/index
:link-type: doc
Development setup, contributing, and the release process.
:::

:::{grid-item-card} Changelog
:link: history
:link-type: doc
Per-package release notes.
:::

::::

## Install

The core query language:

```console
$ pip install django-search-query
```

```console
$ uv add django-search-query
```

The optional Django admin integration (pulls in the core package):

```console
$ pip install django-admin-search-query
```

```console
$ uv add django-admin-search-query
```

See {doc}`quickstart` for developmental releases and next steps.

## What this is

{doc}`django-search-query <packages/django-search-query/index>` accepts a
structured search string and translates it into Django-compatible query
behavior, so an application gets a consistent search syntax without committing
to a particular user interface, admin integration, or search backend. Its
scope is intentionally loose: the syntax is Lucene-inspired without claiming
full Lucene compatibility.

{doc}`django-admin-search-query <packages/django-admin-search-query/index>`
adds that structured search to Django admin pages while keeping the core
language usable on its own. The relationship stays loose so the core package
never couples to admin behavior or presentation concerns. It may also ship a
self-contained, vanilla-JavaScript search input with syntax highlighting,
contextual suggestions, and semantic autocomplete that degrades to a plain
text field when JavaScript is unavailable.

```{note}
Both packages are early scaffolding. The query language and admin integration
are not implemented yet; these docs describe the intended scope.
```

[Lucene]: https://lucene.apache.org/
[Django]: https://docs.djangoproject.com/
[Django admin]: https://docs.djangoproject.com/en/stable/ref/contrib/admin/

```{toctree}
:hidden:

quickstart
packages/index
project/index
history
GitHub <https://github.com/tony/django-search-query>
```
