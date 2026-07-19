"""Query -> Q -> SQL -> rows examples, verified against a real Article set.

The docs' query-language showcase quotes these exact values; this test is
their source of truth (per docs/AGENTS.md: rendered-SQL output is prose to
pytest, checked against a passing test).

SQL is asserted by stable fragments of ``str(qs.query)`` rather than a full
string, so it holds across the Django 5.2/6.0 matrix. The docs render a clean
WHERE clause faithful to those fragments (``str(qs.query)`` itself is Django's
unquoted debug SQL, unfit for display).
"""

from __future__ import annotations

import datetime

import pytest

from django_search_query import search_query_to_q
from test_app.admin import ARTICLE_FIELD_MAP, ARTICLE_REGISTRY
from test_app.models import Article

_DEFAULTS = ("title", "body")
_UTC = datetime.UTC

# (query, expected repr(Q), required SQL fragments, matched titles ordered by created)
CASES: list[tuple[str, str, tuple[str, ...], tuple[str, ...]]] = [
    (
        "status:open",
        "<Q: (AND: ('status__iexact', 'open'))>",
        ('"test_app_article"."status" LIKE open',),
        ("Launch plan", "Report Q3"),
    ),
    (
        "author:tony",
        "<Q: (AND: ('author__icontains', 'tony'))>",
        ('"test_app_article"."author" LIKE %tony%',),
        ("Closed ticket", "Launch plan"),
    ),
    (
        "status:open OR status:draft",
        "<Q: (OR: ('status__iexact', 'open'), ('status__iexact', 'draft'))>",
        ('status" LIKE open', 'status" LIKE draft', " OR "),
        ("Draft memo", "Launch plan", "Report Q3"),
    ),
    (
        "-status:closed",
        "<Q: (NOT (AND: ('status__iexact', 'closed')))>",
        ("NOT (", 'status" LIKE closed'),
        ("Draft memo", "Launch plan", "Report Q3"),
    ),
    (
        "title:report*",
        "<Q: (AND: ('title__istartswith', 'report'))>",
        ('"test_app_article"."title" LIKE report%',),
        ("Report Q3",),
    ),
    (
        "created:>2024-01-01",
        "<Q: (AND: ('created__gt', '2024-01-01'))>",
        ('"test_app_article"."created" > ',),
        ("Draft memo", "Launch plan", "Report Q3"),
    ),
    (
        "status:open author:tony",
        "<Q: (AND: ('status__iexact', 'open'), ('author__icontains', 'tony'))>",
        ('status" LIKE open', 'author" LIKE %tony%', " AND "),
        ("Launch plan",),
    ),
]


@pytest.fixture
def _articles(db: object) -> None:
    Article.objects.create(
        title="Launch plan",
        status="open",
        author="tony",
        body="ship it",
        created=datetime.datetime(2024, 6, 1, tzinfo=_UTC),
    )
    Article.objects.create(
        title="Draft memo",
        status="draft",
        author="jane",
        body="notes",
        created=datetime.datetime(2024, 3, 15, tzinfo=_UTC),
    )
    Article.objects.create(
        title="Closed ticket",
        status="closed",
        author="tony",
        body="wrap up",
        created=datetime.datetime(2023, 11, 20, tzinfo=_UTC),
    )
    Article.objects.create(
        title="Report Q3",
        status="open",
        author="mint",
        body="metrics",
        created=datetime.datetime(2024, 9, 1, tzinfo=_UTC),
    )


# A bare date value against a DateTimeField (``created:>2024-01-01``) is
# compared as a naive datetime under USE_TZ -- expected query behavior, not a
# test defect. Keep the output pristine.
@pytest.mark.filterwarnings(
    "ignore:DateTimeField .* received a naive datetime:RuntimeWarning"
)
@pytest.mark.usefixtures("_articles")
@pytest.mark.parametrize(("query", "expected_q", "sql_fragments", "titles"), CASES)
def test_query_showcase(
    query: str,
    expected_q: str,
    sql_fragments: tuple[str, ...],
    titles: tuple[str, ...],
) -> None:
    """Each query compiles to the pinned Q, SQL fragments, and matched rows."""
    q = search_query_to_q(
        query,
        registry=ARTICLE_REGISTRY,
        field_map=ARTICLE_FIELD_MAP,
        default_fields=_DEFAULTS,
    )
    assert repr(q) == expected_q
    qs = Article.objects.filter(q).order_by("created")
    sql = str(qs.query)
    for fragment in sql_fragments:
        assert fragment in sql, f"{fragment!r} not in {sql!r}"
    assert tuple(a.title for a in qs) == titles
