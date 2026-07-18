(packages)=

# Packages

The workspace ships two independently-installable, independently-versioned
packages. The core query language stands on its own; the admin integration is
opt-in and depends on it through a loose version floor.

## Core

- [`django-search-query`](django-search-query/index.md) -- structured,
  Lucene-inspired search query language that compiles to Django ORM lookups.
  No UI, admin, or backend assumptions.

## Django admin

- [`django-admin-search-query`](django-admin-search-query/index.md) --
  structured search on Django admin changelist pages, plus an optional
  vanilla-JavaScript search input. Built on `django-search-query`.

```{toctree}
:caption: Packages
:hidden:

django-search-query/index
django-admin-search-query/index
```
