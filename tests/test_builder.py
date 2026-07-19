"""Tests for the AST-to-``Q`` compiler."""

from __future__ import annotations

from django.db.models import Q

from django_search_query.ast import (
    And,
    Cmp,
    Exists,
    Field,
    Not,
    Or,
    Range,
    Term,
)
from django_search_query.compiler import build_q

FIELD_MAP = {"status": "status", "author": "author", "created": "created"}
DEFAULTS = ("title", "body")


def test_bare_term_ors_icontains_across_defaults() -> None:
    """A bare term ORs ``icontains`` across every default field."""
    result = build_q(Term(value="hi"), FIELD_MAP, default_fields=DEFAULTS)
    assert result == Q(title__icontains="hi") | Q(body__icontains="hi")


def test_wildcard_suffix_uses_istartswith() -> None:
    """``foo*`` anchors the start with ``istartswith``."""
    result = build_q(Term(value="foo*"), FIELD_MAP, default_fields=("title",))
    assert result == Q(title__istartswith="foo")


def test_wildcard_prefix_uses_iendswith() -> None:
    """``*foo`` anchors the end with ``iendswith``."""
    result = build_q(Term(value="*foo"), FIELD_MAP, default_fields=("title",))
    assert result == Q(title__iendswith="foo")


def test_phrase_uses_icontains_verbatim() -> None:
    """A phrase matches verbatim, ignoring any ``*`` inside it."""
    node = Term(value="a b", is_phrase=True)
    result = build_q(node, FIELD_MAP, default_fields=("title",))
    assert result == Q(title__icontains="a b")


def test_enum_field_uses_iexact() -> None:
    """An enum ``Field`` compiles to ``iexact``."""
    node = Field(field="status", value="open", kind="enum")
    result = build_q(node, FIELD_MAP, default_fields=())
    assert result == Q(status__iexact="open")


def test_string_field_uses_icontains() -> None:
    """A string ``Field`` compiles to ``icontains`` with wildcard rules."""
    node = Field(field="author", value="tony", kind="string")
    result = build_q(node, FIELD_MAP, default_fields=())
    assert result == Q(author__icontains="tony")


def test_field_map_resolves_orm_path() -> None:
    """The field map rewrites the field name to its ORM path."""
    node = Field(field="author", value="tony", kind="string")
    result = build_q(node, {"author": "writer__name"}, default_fields=())
    assert result == Q(writer__name__icontains="tony")


def test_comparison_uses_operator_suffix() -> None:
    """A ``Cmp`` compiles to the matching lookup suffix."""
    node = Cmp(field="created", op="gte", value="2024-01-01")
    result = build_q(node, FIELD_MAP, default_fields=())
    assert result == Q(created__gte="2024-01-01")


def test_inclusive_range_bounds_both_sides() -> None:
    """An inclusive range compiles to ``gte`` AND ``lte``."""
    node = Range(
        field="created",
        lo="2024",
        hi="2025",
        inclusive_lo=True,
        inclusive_hi=True,
    )
    result = build_q(node, FIELD_MAP, default_fields=())
    assert result == Q(created__gte="2024") & Q(created__lte="2025")


def test_range_star_bound_is_open() -> None:
    """A ``*`` bound omits that side of the range."""
    node = Range(
        field="created",
        lo="*",
        hi="2025",
        inclusive_lo=False,
        inclusive_hi=False,
    )
    result = build_q(node, FIELD_MAP, default_fields=())
    assert result == Q(created__lt="2025")


def test_exists_checks_present_and_non_empty() -> None:
    """``Exists`` excludes empty strings and NULLs."""
    result = build_q(Exists(field="author"), FIELD_MAP, default_fields=())
    assert result == ~Q(author="") & ~Q(author__isnull=True)


def test_not_negates_child() -> None:
    """``Not`` negates the compiled child ``Q``."""
    node = Not(child=Field(field="status", value="open", kind="enum"))
    result = build_q(node, FIELD_MAP, default_fields=())
    assert result == ~Q(status__iexact="open")


def test_and_or_combine_children() -> None:
    """``And``/``Or`` fold children with ``&``/``|``."""
    status = Field(field="status", value="open", kind="enum")
    author = Field(field="author", value="tony", kind="string")
    and_q = build_q(And(children=(status, author)), FIELD_MAP, default_fields=())
    assert and_q == Q(status__iexact="open") & Q(author__icontains="tony")
    or_q = build_q(Or(children=(status, author)), FIELD_MAP, default_fields=())
    assert or_q == Q(status__iexact="open") | Q(author__icontains="tony")
