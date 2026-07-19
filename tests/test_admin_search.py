"""Tests for the Django admin search-query mixin."""

from __future__ import annotations

import typing as t

import pytest
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone

from django_admin_search_query.mixin import _strip_search_field_prefixes
from test_app.admin import ArticleAdmin
from test_app.models import Article

if t.TYPE_CHECKING:
    from django.test import Client
    from django.test.client import RequestFactory


def test_strip_search_field_prefixes() -> None:
    """Django ``search_fields`` sigils are stripped for bare-term defaults."""
    stripped = _strip_search_field_prefixes(
        ("^title", "=body", "@content", "$slug", "author"),
    )
    assert stripped == ("title", "body", "content", "slug", "author")


@pytest.fixture
def articles(db: object) -> None:
    """Create one matching and one non-matching article row."""
    now = timezone.now()
    Article.objects.create(
        title="Open one",
        status="open",
        author="tony",
        body="hello",
        created=now,
    )
    Article.objects.create(
        title="Draft two",
        status="draft",
        author="jane",
        body="world",
        created=now,
    )


@pytest.mark.django_db
def test_mixin_filters_queryset(rf: RequestFactory, articles: None) -> None:
    """The mixin parses a structured term and filters the queryset."""
    model_admin = ArticleAdmin(Article, admin.site)
    request = rf.get("/admin/test_app/article/")
    queryset, may_have_duplicates = model_admin.get_search_results(
        request,
        Article.objects.all(),
        "status:open author:tony",
    )
    assert may_have_duplicates is False
    assert list(queryset.values_list("title", flat=True)) == ["Open one"]


@pytest.mark.django_db
def test_mixin_empty_term_returns_all(rf: RequestFactory, articles: None) -> None:
    """An empty search term falls back to Django's default search."""
    model_admin = ArticleAdmin(Article, admin.site)
    request = rf.get("/admin/test_app/article/")
    queryset, _ = model_admin.get_search_results(
        request,
        Article.objects.all(),
        "",
    )
    assert queryset.count() == 2


@pytest.mark.django_db
def test_mixin_degrades_on_parse_error(rf: RequestFactory, articles: None) -> None:
    """An unparseable term degrades to default search without raising."""
    model_admin = ArticleAdmin(Article, admin.site)
    request = rf.get("/admin/test_app/article/")
    queryset, _ = model_admin.get_search_results(
        request,
        Article.objects.all(),
        '"unterminated',
    )
    # Default search over title/body finds nothing for the literal text.
    assert queryset.count() == 0


@pytest.mark.django_db
def test_changelist_view_filters(admin_client: Client, articles: None) -> None:
    """The admin changelist applies the structured query from ``?q=``."""
    url = reverse("admin:test_app_article_changelist")
    response = admin_client.get(url, {"q": "status:open author:tony"})
    assert response.status_code == 200
    changelist = response.context["cl"]
    assert list(changelist.queryset.values_list("title", flat=True)) == ["Open one"]
