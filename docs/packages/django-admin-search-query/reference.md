(admin-search-query-reference)=

# Reference

{class}`~django_admin_search_query.mixin.SearchQueryAdminMixin` is the one
class this package ships: mount it ahead of
{class}`~django.contrib.admin.ModelAdmin` (see {doc}`how-to`) and it wires
the structured query language into
{meth}`~django.contrib.admin.ModelAdmin.get_search_results`, adds two JSON
endpoints behind the colored input, and injects the URLs those endpoints
need into the changelist template. Everything below is optional
configuration on top of that one mixin -- most sites only ever set the three
class attributes from the how-to guide.

## Public API

```{eval-rst}
.. autoclass:: django_admin_search_query.mixin.SearchQueryAdminMixin
   :members:
```

## Hook contracts

Each class attribute has a matching `get_*` method, so dynamic behavior --
a registry that depends on `request.user`, say -- only needs to override the
method, not chase every place the attribute is read. Called with no
overrides, the hooks read the class attributes straight through, and
`get_search_query_default_fields` falls back to
{attr}`~django.contrib.admin.ModelAdmin.search_fields` (stripped of Django's
lookup sigils -- `^`, `=`, `@`, `$`) whenever `search_query_default_fields`
is left empty:

```{doctest}
>>> from django_admin_search_query.mixin import SearchQueryAdminMixin
>>> class ExampleAdmin(SearchQueryAdminMixin):
...     search_fields = ("^title", "=slug")
>>> ExampleAdmin().get_search_query_default_fields()
('title', 'slug')
```

{meth}`~django_admin_search_query.mixin.SearchQueryAdminMixin.get_search_results`
is the method Django's changelist actually calls. It strips the search
term, and returns `super().get_search_results(...)` unchanged -- Django's
own `search_fields` behavior -- whenever the term is blank, no registry is
configured, or
{exc}`~django_search_query.errors.QueryParseError` is raised while
compiling it; otherwise it returns `queryset.filter(q), False`. The `bool`
is always `False`: filtering by `Q` here introduces no joins that would
make Django's duplicate-row handling necessary.

## JSON endpoints

{meth}`~django_admin_search_query.mixin.SearchQueryAdminMixin.get_urls`
prepends two model-scoped endpoints to the admin's URLs, each wrapped in
`admin_site.admin_view` so it inherits the admin's staff-login gate, and
each additionally checking
{meth}`~django.contrib.admin.ModelAdmin.has_view_permission` before
responding:

- `search-tokens/` (named `<app>_<model>_search_tokens`) -- the registry's
  fields, kinds, operators, enum values, and default fields, as
  {class}`~django.http.JsonResponse`.
- `search-highlight/` (named `<app>_<model>_search_highlight`) -- the
  highlight spans for a `?q=` query string, as
  {class}`~django.http.JsonResponse`.

Both endpoints are always registered once the mixin is mounted. The
changelist template only *advertises* them -- as `data-*` attributes the
colored input reads -- when `search_query_registry` is configured; without
a registry, the search box renders as stock admin with no extra markup. See
{doc}`colored-input` for the exact JSON shape of each endpoint and how the
JavaScript input consumes it.
