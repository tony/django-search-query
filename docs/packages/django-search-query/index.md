(django-search-query)=

# django-search-query

A [Lucene]-inspired search query language that compiles to Django
{class}`~django.db.models.Q` objects.

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
Task recipes: map field names, restrict searchable fields, use wildcards and
ranges, and catch parse errors.
:::

:::{grid-item-card} {octicon}`book` Reference
:link: reference
:link-type: doc
The public API and the query-syntax grammar.
:::

:::{grid-item-card} {octicon}`light-bulb` Explanation
:link: explanation
:link-type: doc
How a search string becomes a `Q` object, and why the highlighter uses a
second lexer.
:::

::::

[Lucene]: https://lucene.apache.org/

```{toctree}
:hidden:

how-to
reference
explanation
```
