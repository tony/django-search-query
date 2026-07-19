(packages)=

# Packages

The workspace ships two independently-installable, independently-versioned
packages. The core query language stands on its own; the admin integration is
opt-in and depends on it through a loose version floor.

::::{grid} 1 1 2 2
:gutter: 2 2 3 3

:::{grid-item-card} {octicon}`package` django-search-query
:link: django-search-query/index
:link-type: doc
The core query language: compiles a search string to Django ORM `Q` objects. No UI, admin, or backend assumptions.
:::

:::{grid-item-card} {octicon}`browser` django-admin-search-query
:link: django-admin-search-query/index
:link-type: doc
Optional Django admin integration built on the core, with a vanilla-JavaScript search input. Depends on it through a loose version floor.
:::

::::

```{toctree}
:caption: Packages
:hidden:

django-search-query/index
django-admin-search-query/index
```
