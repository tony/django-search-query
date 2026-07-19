"""Canonical query -> Q examples reused verbatim in the docs.

Pins the exact ``repr(Q)`` so tutorial and reference pages quote a string
that is proven against real behavior.
"""

from __future__ import annotations

import pytest

from django_search_query import search_query_to_q
from test_app.admin import ARTICLE_FIELD_MAP, ARTICLE_REGISTRY

_DEFAULT_FIELDS = ("title", "body")

# (query, expected repr(Q)). Filled from the real reprs observed by running
# the test; never hand-written.
CASES: list[tuple[str, str]] = [
    ("status:open", "<Q: (AND: ('status__iexact', 'open'))>"),
    ('title:"exact phrase"', "<Q: (AND: ('title__icontains', 'exact phrase'))>"),
    ("author:tony", "<Q: (AND: ('author__icontains', 'tony'))>"),
    (
        "status:open OR status:draft",
        "<Q: (OR: ('status__iexact', 'open'), ('status__iexact', 'draft'))>",
    ),
    (
        "status:open author:tony",  # implicit AND by juxtaposition
        "<Q: (AND: ('status__iexact', 'open'), ('author__icontains', 'tony'))>",
    ),
    ("-status:closed", "<Q: (NOT (AND: ('status__iexact', 'closed')))>"),  # NOT
    (
        "title:report*",  # trailing wildcard -> istartswith
        "<Q: (AND: ('title__istartswith', 'report'))>",
    ),
    (
        "created:>2024-01-01",  # comparison
        "<Q: (AND: ('created__gt', '2024-01-01'))>",
    ),
    (
        "created:[2024-01-01 TO 2024-12-31]",  # inclusive range
        "<Q: (AND: ('created__gte', '2024-01-01'), ('created__lte', '2024-12-31'))>",
    ),
    (
        "status:*",  # existence
        "<Q: (AND: (NOT (AND: ('status', ''))), "
        "(NOT (AND: ('status__isnull', True))))>",
    ),
]


@pytest.mark.parametrize(("query", "expected"), CASES)
def test_query_compiles_to_expected_q(query: str, expected: str) -> None:
    """A query string compiles to the exact ``repr(Q)`` quoted in the docs."""
    q = search_query_to_q(
        query,
        registry=ARTICLE_REGISTRY,
        field_map=ARTICLE_FIELD_MAP,
        default_fields=_DEFAULT_FIELDS,
    )
    assert repr(q) == expected
