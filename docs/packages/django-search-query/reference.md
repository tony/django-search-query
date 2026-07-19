(dsq-reference)=

# Reference

{func}`~django_search_query.search_query_to_q` is the one call most sites
need: it chains {func}`~django_search_query.parse` and
{func}`~django_search_query.build_q` for you. Call `parse`/`build_q`
directly only when you want the AST in between -- to inspect or transform it
before compiling, say.
{class}`~django_search_query.registry.FieldRegistry` and
{class}`~django_search_query.registry.FieldSpec` describe the fields a
query may touch, and {exc}`~django_search_query.errors.QueryParseError` is
the one exception every entry point raises on bad input. See
{doc}`explanation` for how the pieces fit together.

## Public API

```{eval-rst}
.. autofunction:: django_search_query.search_query_to_q

.. autofunction:: django_search_query.parse

.. autofunction:: django_search_query.build_q

.. autoclass:: django_search_query.registry.FieldRegistry
   :members:

.. autoclass:: django_search_query.registry.FieldSpec

.. autoclass:: django_search_query.errors.QueryParseError
```

## Query syntax

Every row compiles exactly as shown; the {doc}`how-to guide <how-to>` runs
several of these as doctests.

| Syntax | Example | Compiles to |
| --- | --- | --- |
| Bare term | {dsq}`hello` | `icontains`, OR'd across `default_fields` |
| Quoted phrase | {dsq}`"exact phrase"` | `icontains`, verbatim (no wildcard expansion) |
| String field | {dsq}`author:tony` | `author__icontains='tony'` |
| Enum field | {dsq}`status:open` | `status__iexact='open'` |
| Trailing wildcard | {dsq}`title:report*` | `title__istartswith='report'` |
| Leading wildcard | {dsq}`title:*report` | `title__iendswith='report'` |
| Comparison | {dsq}`created:>2024-01-01` | `created__gt='2024-01-01'` |
| Inclusive range | {dsq}`created:[2024-01-01 TO 2024-12-31]` | `created__gte='2024-01-01'` and `created__lte='2024-12-31'` |
| Exclusive range | {dsq}`created:{2024-01-01 TO 2024-12-31}` | `created__gt='2024-01-01'` and `created__lt='2024-12-31'` |
| Existence | {dsq}`status:*` | `status` is non-empty and non-null |
| OR | {dsq}`status:open OR status:draft` | `Q(...) \| Q(...)` |
| Implicit AND | {dsq}`status:open author:tony` | `Q(...) & Q(...)` |
| Negation | {dsq}`-status:closed` | `~Q(status__iexact='closed')` |
| `?` (reserved) | {dsq}`title:a?c` | literal `title__icontains='a?c'` -- `?` is not a wildcard the compiler implements |
| Bare value on a `date`/`number` field | {dsq}`created:2024` | literal `created__icontains='2024'` -- not a date or number comparison |

The last two rows are deliberate, not bugs: `?` is a wildcard character to
the highlighter only, and a field's `kind` controls formatting, not parsing
-- a bare value never becomes a Python `date` or `int` before it reaches the
ORM. See {doc}`explanation` for why.
