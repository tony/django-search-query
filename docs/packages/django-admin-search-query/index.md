(django-admin-search-query)=

# django-admin-search-query

An optional Django admin integration for
{doc}`django-search-query <../django-search-query/index>` -- reach for it
when you want a changelist search box that understands the structured query
language; the core package works without it.

::::{grid} 1 1 2 2
:gutter: 2 2 3 3

:::{grid-item-card} {octicon}`rocket` Tutorial
:link: ../../tutorial
:link-type: doc
Build a search registry and run a query against a Django queryset.
:::

:::{grid-item-card} {octicon}`checklist` How-to
:link: how-to
:link-type: doc
Add `SearchQueryAdminMixin` to a `ModelAdmin`, using the worked `ArticleAdmin`
example.
:::

:::{grid-item-card} {octicon}`book` API reference
:link: ../../api
:link-type: doc
The `SearchQueryAdminMixin` API, its hooks, and the JSON endpoints behind the
colored input.
:::

:::{grid-item-card} {octicon}`light-bulb` Explanation
:link: explanation
:link-type: doc
Loose coupling to the core package, and how the search box degrades without
JavaScript.
:::

:::{grid-item-card} {octicon}`paintbrush` Colored input
:link: colored-input
:link-type: doc
The optional vanilla-JavaScript search input: syntax highlighting and
autocomplete.
:::

::::

```{toctree}
:hidden:

how-to
explanation
colored-input
```
