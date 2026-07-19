(admin-search-query-how-to)=

# How-to guides

{class}`~django_admin_search_query.mixin.SearchQueryAdminMixin` is opt-in --
drop it in front of a {class}`~django.contrib.admin.ModelAdmin` on the
changelists that need structured search, and leave every other admin
untouched.

## Add structured search to a ModelAdmin

Put the mixin *before* `admin.ModelAdmin` in the base list. Python resolves
methods left to right, so the mixin's {meth}`~django.contrib.admin.ModelAdmin.get_search_results`
and {meth}`~django.contrib.admin.ModelAdmin.get_urls` run first and call
`super()` to reach Django's own implementation -- reversing the order would
skip the mixin entirely.

This is the real registration the project tests against, from
`test_app/admin.py`:

```python
from django.contrib import admin

from django_admin_search_query import SearchQueryAdminMixin
from django_search_query.registry import FieldRegistry, FieldSpec

from .models import Article

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

ARTICLE_FIELD_MAP = {spec.name: spec.path for spec in ARTICLE_REGISTRY.specs}


@admin.register(Article)
class ArticleAdmin(SearchQueryAdminMixin, admin.ModelAdmin):
    list_display = ("title", "status", "author", "created")
    search_fields = ("title", "body")
    search_query_registry = ARTICLE_REGISTRY
    search_query_field_map = ARTICLE_FIELD_MAP
    search_query_default_fields = ("title", "body")
```

Three class attributes wire the language into this admin:

- `search_query_registry` -- the same kind of
  {class}`~django_search_query.registry.FieldRegistry` you would build for
  any other site; it decides which fields {dsq}`status:open` and friends may
  touch on this changelist.
- `search_query_field_map` -- field name to ORM lookup path, exactly like
  the core package's `field_map` (see {doc}`../django-search-query/how-to`).
- `search_query_default_fields` -- ORM paths a bare term or phrase searches.

`search_fields` stays in place and keeps doing double duty: it is still
{attr}`~django.contrib.admin.ModelAdmin.search_fields`, so it is what a bare
term falls back to when `search_query_default_fields` is left unset, and it
is also where Django's own search takes over whenever the query does not
parse -- a plain word, an unterminated quote, an unknown field. Set
`search_query_registry` and the box upgrades to structured search; leave it
unset and the admin behaves exactly like stock `ModelAdmin.search_fields`,
so you can add the mixin ahead of writing a registry without changing
behavior. See {doc}`explanation` for why that fallback never regresses the
box below stock admin, and {doc}`colored-input` for the optional
syntax-highlighting input that comes with the mixin.
