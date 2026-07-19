"""Tests for the Pratt precedence-climbing parser."""

from __future__ import annotations

import pytest

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
from django_search_query.errors import QueryParseError
from django_search_query.parser import parse
from django_search_query.registry import FieldRegistry, FieldSpec

REGISTRY = FieldRegistry(
    specs=(
        FieldSpec(name="title", kind="string"),
        FieldSpec(name="author", kind="string", aliases=("by",)),
        FieldSpec(name="status", kind="enum", enum_values=("open", "draft")),
        FieldSpec(
            name="created",
            kind="date",
            supports_comparison=True,
            supports_range=True,
        ),
    ),
)


def test_single_term_is_not_wrapped() -> None:
    """A lone term parses to a bare ``Term`` (no one-child And/Or)."""
    assert parse("bliss", REGISTRY) == Term(value="bliss")


def test_implicit_and_is_flattened() -> None:
    """Adjacent primaries flatten into one n-ary ``And``."""
    assert parse("a b c", REGISTRY) == And(
        children=(Term(value="a"), Term(value="b"), Term(value="c")),
    )


def test_or_binds_looser_than_implicit_and() -> None:
    """``a OR b c`` groups as ``a OR (b AND c)``."""
    assert parse("a OR b c", REGISTRY) == Or(
        children=(
            Term(value="a"),
            And(children=(Term(value="b"), Term(value="c"))),
        ),
    )


def test_and_binds_tighter_than_or_on_the_left() -> None:
    """``a b OR c`` groups as ``(a AND b) OR c``."""
    assert parse("a b OR c", REGISTRY) == Or(
        children=(
            And(children=(Term(value="a"), Term(value="b"))),
            Term(value="c"),
        ),
    )


def test_not_is_a_tight_prefix() -> None:
    """``NOT a AND b`` groups as ``(NOT a) AND b``."""
    assert parse("NOT a AND b", REGISTRY) == And(
        children=(Not(child=Term(value="a")), Term(value="b")),
    )


def test_minus_sigil_is_negation() -> None:
    """A leading ``-`` parses to the same node as ``NOT``."""
    assert parse("-draft", REGISTRY) == Not(child=Term(value="draft"))


def test_grouping_overrides_precedence() -> None:
    """Parentheses force ``(a OR b) AND c``."""
    assert parse("(a OR b) c", REGISTRY) == And(
        children=(
            Or(children=(Term(value="a"), Term(value="b"))),
            Term(value="c"),
        ),
    )


def test_phrase_term_is_flagged() -> None:
    """A quoted phrase parses to a phrase-flagged ``Term``."""
    assert parse('"exact phrase"', REGISTRY) == Term(
        value="exact phrase",
        is_phrase=True,
    )


def test_field_alias_resolves_to_canonical_name() -> None:
    """An aliased field resolves to its canonical name and kind."""
    assert parse("by:tony", REGISTRY) == Field(
        field="author",
        value="tony",
        kind="string",
    )


def test_enum_field_carries_its_kind() -> None:
    """An enum field's spec kind rides along on the ``Field`` node."""
    assert parse("status:open", REGISTRY) == Field(
        field="status",
        value="open",
        kind="enum",
    )


def test_field_star_is_exists() -> None:
    """``field:*`` parses to an ``Exists`` node."""
    assert parse("title:*", REGISTRY) == Exists(field="title")


def test_comparison_parses_to_cmp() -> None:
    """``field:>value`` parses to a ``Cmp`` node."""
    assert parse("created:>=2024-01-01", REGISTRY) == Cmp(
        field="created",
        op="gte",
        value="2024-01-01",
    )


def test_inclusive_range_parses_to_range() -> None:
    """``[a TO b]`` parses to an inclusive ``Range``."""
    assert parse("created:[2024 TO 2025]", REGISTRY) == Range(
        field="created",
        lo="2024",
        hi="2025",
        inclusive_lo=True,
        inclusive_hi=True,
    )


def test_exclusive_range_parses_to_range() -> None:
    """``{a TO b}`` parses to an exclusive ``Range``."""
    assert parse("created:{2024 TO 2025}", REGISTRY) == Range(
        field="created",
        lo="2024",
        hi="2025",
        inclusive_lo=False,
        inclusive_hi=False,
    )


def test_unknown_field_raises_positioned_error() -> None:
    """An unknown field raises a positioned error listing known fields."""
    with pytest.raises(QueryParseError) as excinfo:
        parse("bogus:x", REGISTRY)
    assert excinfo.value.position == 0
    assert "title" in str(excinfo.value)


def test_comparison_on_unsupported_field_raises() -> None:
    """Comparison on a non-ordered field is rejected at parse time."""
    with pytest.raises(QueryParseError):
        parse("title:>x", REGISTRY)


def test_range_on_unsupported_field_raises() -> None:
    """Range on a non-ordered field is rejected at parse time."""
    with pytest.raises(QueryParseError):
        parse("title:[1 TO 2]", REGISTRY)


def test_unbalanced_group_raises() -> None:
    """A missing closing paren raises a parse error."""
    with pytest.raises(QueryParseError):
        parse("(a b", REGISTRY)
