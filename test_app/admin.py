"""Admin registration wiring the query language onto :class:`Article`."""

from __future__ import annotations

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
    """Changelist admin for :class:`Article` with structured search."""

    list_display = ("title", "status", "author", "created")
    search_fields = ("title", "body")
    search_query_registry = ARTICLE_REGISTRY
    search_query_field_map = ARTICLE_FIELD_MAP
    search_query_default_fields = ("title", "body")
