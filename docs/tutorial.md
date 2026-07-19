(tutorial)=

# Tutorial

This tutorial builds one search-enabled queryset from a raw string. You
describe which fields a query is allowed to touch, compile a query string
into a Django {class}`~django.db.models.Q`, and run it against a real
{class}`~django.db.models.QuerySet`. That is the whole path -- most projects
never need more than this.

## Describe your searchable fields

`search_query_to_q` needs to know which fields a query string may touch, and
what kind of value each one holds -- a plain string, an enum, a date. You
declare that once with a `FieldRegistry` built from `FieldSpec` entries; the
registry is what turns `status:open` into a validated lookup instead of an
arbitrary attribute access.

A registry for an `Article` model with a title, a body, an author, a status,
and a creation date looks like this:

```python
from django_search_query.registry import FieldRegistry, FieldSpec

ARTICLE_REGISTRY = FieldRegistry(
    specs=(
        FieldSpec(name="title", kind="string"),
        FieldSpec(name="body", kind="string"),
        FieldSpec(name="author", kind="string"),
        FieldSpec(
            name="status",
            kind="enum",
            enum_values=("open", "draft", "closed"),
        ),
        FieldSpec(
            name="created",
            kind="date",
            supports_comparison=True,
            supports_range=True,
        ),
    ),
)
```

This tutorial only queries `status`, so the rest of it works with a
single-field registry.

## Compile a query

`search_query_to_q` takes the query string, the registry, a field map
(canonical field name to ORM lookup path), and which fields a bare term or
phrase searches by default -- then returns a `Q` you pass straight to
`.filter()`.

```{doctest}
>>> from django_search_query import search_query_to_q
>>> from django_search_query.registry import FieldRegistry, FieldSpec
>>> registry = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
>>> search_query_to_q(
...     "status:open",
...     registry=registry,
...     field_map={"status": "status"},
...     default_fields=("title", "body"),
... )
<Q: (AND: ('status__iexact', 'open'))>
```

`status:open` matched the `status` field spec, so it compiled to an
`__iexact` lookup on the `status` column. Terms without a `field:` prefix
would instead search every path listed in `default_fields`.

## Run it against a queryset

The `Q` above is unremarkable to Django -- pass it to `.filter()` like any
other:

```python
q = search_query_to_q(
    "status:open",
    registry=registry,
    field_map={"status": "status"},
    default_fields=("title", "body"),
)
Article.objects.filter(q)
```

This snippet is illustrative rather than an executed doctest: filtering a
real queryset needs a migrated `Article` table, which the docs build does not
provide. `tests/test_query_examples.py` pins the exact `Q` this `status:open`
call compiles to, so the claim above stays checked against real behavior.

## Where to go next

- {doc}`install` -- add the packages to a project and read about
  developmental releases.
- {doc}`packages/django-search-query/index` -- the field-map dict, allowed
  fields, validation hooks, and the syntax the parser accepts.
- {doc}`packages/django-admin-search-query/index` -- the opt-in admin
  integration and its JavaScript search input.
