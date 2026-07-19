(dsq-how-to)=

# How-to guides

Task recipes for tuning {func}`~django_search_query.search_query_to_q`
beyond the tutorial's defaults: which ORM path a field name resolves to,
which fields a query may touch at all, how wildcards and ranges compile, and
how to degrade gracefully when a query does not parse.

## Map field names to ORM paths

`field_map` decouples the field name a user types from the ORM lookup path
the compiler builds. A registered field defaults to its own name when
`field_map` leaves it out, so most sites only add an entry for a field whose
ORM path really differs -- an alias, or a lookup that crosses a relation with
Django's `__` traversal.

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(specs=(FieldSpec(name="author", kind="string"),))
>>> search_query_to_q(
...     "author:tony",
...     registry=registry,
...     field_map={"author": "author"},
...     default_fields=("title", "body"),
... )
<Q: (AND: ('author__icontains', 'tony'))>
```

`field_map={}` would compile identically here, since `author`'s ORM path
already matches its name.

## Restrict which fields a query can touch

A {class}`~django_search_query.registry.FieldRegistry` is a strict allow
list: only names declared as a
{class}`~django_search_query.registry.FieldSpec` are queryable. A term for
anything else -- a stray internal field, a typo -- raises
{exc}`~django_search_query.errors.QueryParseError` at parse time instead of
silently matching nothing.

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(
...     specs=(
...         FieldSpec(name="title", kind="string"),
...         FieldSpec(name="status", kind="enum"),
...     ),
... )
>>> search_query_to_q(
...     "status:open",
...     registry=registry,
...     field_map={},
...     default_fields=("title",),
... )
<Q: (AND: ('status__iexact', 'open'))>
```

`status` is declared, so it compiles; a query for a field the registry never
listed raises -- see {ref}`dsq-how-to-fallback` for how to catch that.

## Wildcards and ranges

String fields support two wildcards: a trailing `*` anchors the match to the
start of the value (`istartswith`), a leading `*` anchors it to the end
(`iendswith`); a bare value, or one wrapped in `*` on both sides, stays
`icontains`. A `date` or `number` field whose
{class}`~django_search_query.registry.FieldSpec` opts in also accepts
ordered comparisons (`>`, `>=`, `<`, `<=`) and inclusive or exclusive ranges
(`[a TO b]` / `{a TO b}`).

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(specs=(FieldSpec(name="title", kind="string"),))
>>> search_query_to_q(
...     "title:report*",
...     registry=registry,
...     field_map={},
...     default_fields=(),
... )
<Q: (AND: ('title__istartswith', 'report'))>
```

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(
...     specs=(FieldSpec(name="created", kind="date", supports_range=True),),
... )
>>> search_query_to_q(
...     "created:[2024-01-01 TO 2024-12-31]",
...     registry=registry,
...     field_map={},
...     default_fields=(),
... )
<Q: (AND: ('created__gte', '2024-01-01'), ('created__lte', '2024-12-31'))>
```

`?` looks like it should be a single-character wildcard, Lucene-style -- it
is not. The presentation lexer that drives syntax highlighting recognizes
`?` as a `wildcard`-role character (see {doc}`explanation`), but the
compiler only ever implements `*`. A literal `?` in a value passes straight
through to `icontains`:

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(specs=(FieldSpec(name="title", kind="string"),))
>>> search_query_to_q(
...     "title:a?c",
...     registry=registry,
...     field_map={},
...     default_fields=(),
... )
<Q: (AND: ('title__icontains', 'a?c'))>
```

A bare value on a `date` or `number` field is not parsed into a date or
number either -- without a comparison or range operator it takes the same
`icontains` path as a string field:

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(specs=(FieldSpec(name="created", kind="date"),))
>>> search_query_to_q(
...     "created:2024",
...     registry=registry,
...     field_map={},
...     default_fields=(),
... )
<Q: (AND: ('created__icontains', '2024'))>
```

(dsq-how-to-fallback)=

## Catch parse errors and fall back

Any malformed query -- an unknown field, an unsupported operator, an
unterminated quote -- raises
{exc}`~django_search_query.errors.QueryParseError` with the character offset
of the failure. A search endpoint that always needs to return *something*
can catch it and fall back to a plain substring search:

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.errors import QueryParseError
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
>>> try:
...     search_query_to_q(
...         "bogus:1", registry=registry, field_map={}, default_fields=("title",),
...     )
... except QueryParseError as err:
...     print(f"fell back: {err}")
fell back: unknown field 'bogus'; known fields: status
```

`err.position` is the offset into the original string -- handy for pointing
a caret at the exact character that broke.
{doc}`../django-admin-search-query/colored-input` uses the same lexer output
to color a live search box.
