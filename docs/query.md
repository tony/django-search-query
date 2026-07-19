(query)=

# Query language

You give your users a real search box -- field-scoped terms, quoted phrases,
boolean logic -- and {func}`~django_search_query.search_query_to_q` turns what
they type into a Django {class}`~django.db.models.Q`. Pass that to any
{class}`~django.db.models.QuerySet` and the ORM does the rest: **string in,
queryset out**. A field map plus that one call covers most sites, so if the
defaults fit you can stop after the {doc}`tutorial`.

The syntax is Lucene-*inspired*, not Lucene-compatible -- familiar forms mostly
just work, and half-typed or unparseable input degrades to a match instead of
raising. Underneath, a tokenizer lexes the string, {func}`~django_search_query.parse`
builds an AST, and {func}`~django_search_query.build_q` compiles it to a `Q`;
{doc}`the pipeline <packages/django-search-query/explanation>` walks that chain.

## See it work

Seed a handful of articles:

| title | status | author | created |
| --- | --- | --- | --- |
| Launch plan | open | tony | 2024-06-01 |
| Draft memo | draft | jane | 2024-03-15 |
| Closed ticket | closed | tony | 2023-11-20 |
| Report Q3 | open | mint | 2024-09-01 |

Each search string compiles to a `Q`, and {class}`~django.db.models.QuerySet`
`.filter(q)` runs it as SQL:

| You type | It returns | The SQL Django runs |
| --- | --- | --- |
| {dsq}`status:open` | Launch plan, Report Q3 | `WHERE status LIKE 'open'` |
| {dsq}`author:tony` | Closed ticket, Launch plan | `WHERE author LIKE '%tony%'` |
| {dsq}`status:open OR status:draft` | Draft memo, Launch plan, Report Q3 | `WHERE status LIKE 'open' OR status LIKE 'draft'` |
| {dsq}`-status:closed` | Draft memo, Launch plan, Report Q3 | `WHERE NOT (status LIKE 'closed')` |
| {dsq}`title:report*` | Report Q3 | `WHERE title LIKE 'report%'` |
| {dsq}`created:>2024-01-01` | Draft memo, Launch plan, Report Q3 | `WHERE created > '2024-01-01'` |
| {dsq}`status:open author:tony` | Launch plan | `WHERE status LIKE 'open' AND author LIKE '%tony%'` |

Every row is checked against a live `Article` table in
`tests/test_query_showcase.py`, so the SQL and matches stay honest. (The SQL is
cleaned for reading; `str(qs.query)` renders Django's fuller debug form.)

Here is the `Q` behind the first row -- the whole magic in one call:

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
>>> q = search_query_to_q(
...     "status:open",
...     registry=registry,
...     field_map={"status": "status"},
...     default_fields=("title", "body"),
... )
>>> q
<Q: (AND: ('status__iexact', 'open'))>
```

`Article.objects.filter(q)` then returns the matching rows.

## Syntax

Every row compiles exactly as shown. `default_fields` is where bare terms and
phrases search; a {class}`~django_search_query.registry.FieldRegistry` decides
which `field:` names are allowed and how each compiles.

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

The last two rows are deliberate, not bugs: `?` is a wildcard character to the
highlighter only, and a field's `kind` controls formatting, not parsing -- a
bare value never becomes a Python `date` or `int` before it reaches the ORM.

## Next

- {doc}`tutorial` -- build a {class}`~django_search_query.registry.FieldRegistry` and run a query end to end.
- {doc}`api` -- {func}`~django_search_query.search_query_to_q`, {func}`~django_search_query.parse`, {func}`~django_search_query.build_q`, and the field registry.
- {doc}`How-to guides <packages/django-search-query/how-to>` -- field maps, restricting fields, wildcards and ranges, catching {exc}`~django_search_query.errors.QueryParseError`.
- {doc}`Admin integration <packages/django-admin-search-query/index>` -- put this in the Django admin changelist.
