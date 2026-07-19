(admin-search-query-explanation)=

# Explanation

## Loose coupling to the core package

`django-admin-search-query` depends on `django-search-query` through an
ordinary version floor in its `pyproject.toml`
(`django-search-query>=0.1.0a0`), the same way any other consumer of the
query language would. There is no private coupling underneath that pin: the
mixin only ever calls the same public surface documented in
{doc}`../../api` --
{func}`~django_search_query.search_query_to_q`,
{exc}`~django_search_query.errors.QueryParseError`, and the highlighter that
backs {doc}`colored-input`. Nothing in the core package imports or knows
about the admin integration at all; the dependency arrow points one way.

That looseness is deliberate. `django-search-query` stays usable in any
Django project -- a REST endpoint, a management command, a plain view --
whether or not the admin is even installed. The admin integration is the
optional layer built on top, not a requirement the core package carries for
everyone.

## No-JavaScript degradation

The colored input is a progressive enhancement of an admin feature that
already works: the stock `<input id=searchbar>` and Django's own
`search_fields` matching.
{class}`~django_admin_search_query.mixin.SearchQueryAdminMixin` renders the
search box through a per-admin `change_list.html` that calls
`{{ block.super }}` to render Django's own search form untouched -- facets,
hidden filter parameters, and help text stay whatever the installed Django
version renders -- and only adds one thing after it: a hidden `data-*` config
element carrying the URLs of the `search-tokens/` and `search-highlight/`
endpoints (see {doc}`../../api`), emitted only when `search_query_registry`
is set.

`search-input.js` reads that config element on load, finds the stock
`#searchbar` input next to it, and enhances it into the colored editor
described in {doc}`colored-input`. If JavaScript never runs -- disabled,
blocked, or the request never reaches the browser at all -- the config
element is inert markup and `#searchbar` is still the plain Django input:
typing and submitting the form sends `?q=` exactly as it always did, and
the mixin still compiles it server-side. The search box never depends on
JavaScript to function; JavaScript only makes it nicer to type into.

The same fallback also covers a query that *is* JavaScript-typed but does
not parse. A half-finished quote, an unknown field, a stray operator --
anything that raises {exc}`~django_search_query.errors.QueryParseError` (or
an empty term, or an admin with no `search_query_registry` configured) makes
{meth}`~django_admin_search_query.mixin.SearchQueryAdminMixin.get_search_results`
fall back to `super().get_search_results(...)`, Django's own
`search_fields` behavior. No-JS submissions and unparseable JS submissions
land on the same code path, so the admin search box is never worse than
stock `ModelAdmin` -- only ever better, when the query happens to parse.
