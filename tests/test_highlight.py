"""Tests for the whole-string highlight lexer."""

from __future__ import annotations

import pytest

from django_search_query.highlight import (
    HIGHLIGHT_ROLES,
    Span,
    apply_registry_errors,
    highlight_query_spans,
)
from django_search_query.registry import FieldRegistry, FieldSpec

REGISTRY = FieldRegistry(
    specs=(
        FieldSpec(name="title", kind="string"),
        FieldSpec(name="author", kind="string", aliases=("by",)),
        FieldSpec(name="status", kind="enum", enum_values=("open", "draft", "closed")),
        FieldSpec(
            name="created",
            kind="date",
            supports_comparison=True,
            supports_range=True,
        ),
    ),
)


@pytest.mark.parametrize(
    "query",
    [
        "",
        "   ",
        "hello world",
        "status:open",
        'status:open author:tony "exact phrase" NOT draft',
        "-draft +open",
        "created:>=2024-01-01",
        "created:[2024-01-01 TO 2024-12-31]",
        "created:{a TO b}",
        "(a OR b) AND c",
        "foo* *bar a?c",
        'unterminated "phrase',
        "unterminated 'phrase",
        "weird % ^ chars",
        "status:*",
        "tab\tand\nnewline",
    ],
)
def test_spans_cover_the_whole_string(query: str) -> None:
    """Every character is covered exactly once, in order."""
    spans = highlight_query_spans(query)
    assert "".join(span.text for span in spans) == query
    offset = 0
    for span in spans:
        assert span.start == offset
        offset += len(span.text)


@pytest.mark.parametrize(
    "query",
    [
        'a "b',
        "'unterminated",
        "((((",
        "]]]]",
        ">=<=><",
        "\\",
        "🙂 status:open",
    ],
)
def test_never_raises_on_malformed_input(query: str) -> None:
    """Malformed or exotic input still lexes without raising."""
    spans = highlight_query_spans(query)
    assert "".join(span.text for span in spans) == query


def test_roles_are_from_the_published_vocabulary() -> None:
    """The plain lexer only ever emits documented, non-error roles."""
    spans = highlight_query_spans(
        'status:open author:tony "phrase" NOT -draft created:>2024-01-01 a*',
    )
    roles = {span.role for span in spans}
    assert roles <= HIGHLIGHT_ROLES
    assert "error" not in roles


def test_field_and_punct_and_value_split() -> None:
    """A ``field:value`` predicate splits into three spans."""
    assert highlight_query_spans("status:open") == [
        Span(0, "field", "status"),
        Span(6, "punct", ":"),
        Span(7, "value", "open"),
    ]


def test_unterminated_phrase_is_one_span() -> None:
    """An unterminated quote is a single phrase span, not an error."""
    spans = highlight_query_spans('title:"half open')
    assert spans[-1] == Span(6, "phrase", '"half open')


def test_leading_sigil_is_negation_but_internal_hyphen_is_value() -> None:
    """A leading ``-`` colors as negation; a hyphen inside a value does not."""
    assert highlight_query_spans("-draft") == [
        Span(0, "negation", "-"),
        Span(1, "value", "draft"),
    ]
    assert highlight_query_spans("2024-01-01") == [Span(0, "value", "2024-01-01")]


def test_apply_registry_errors_flags_unknown_field() -> None:
    """An unknown field and its value both become ``error`` spans."""
    spans = apply_registry_errors(highlight_query_spans("bogus:value"), REGISTRY)
    assert [(s.role, s.text) for s in spans] == [
        ("error", "bogus"),
        ("punct", ":"),
        ("error", "value"),
    ]


def test_apply_registry_errors_flags_out_of_enum_value() -> None:
    """An out-of-enum value becomes an ``error`` span; the field stays a field."""
    spans = apply_registry_errors(highlight_query_spans("status:bogus"), REGISTRY)
    assert [(s.role, s.text) for s in spans] == [
        ("field", "status"),
        ("punct", ":"),
        ("error", "bogus"),
    ]


def test_apply_registry_errors_accepts_valid_enum_and_alias() -> None:
    """Valid enum values and aliased fields are left unchanged."""
    valid = apply_registry_errors(highlight_query_spans("status:open"), REGISTRY)
    assert all(span.role != "error" for span in valid)
    aliased = apply_registry_errors(highlight_query_spans("by:tony"), REGISTRY)
    assert all(span.role != "error" for span in aliased)


def test_apply_registry_errors_ignores_non_enum_string_field() -> None:
    """A free-text field accepts any value without an error role."""
    spans = apply_registry_errors(highlight_query_spans("title:anything"), REGISTRY)
    assert all(span.role != "error" for span in spans)


def test_apply_registry_errors_does_not_mutate_input() -> None:
    """The second pass returns a new list and leaves the input untouched."""
    original = highlight_query_spans("bogus:value")
    snapshot = list(original)
    apply_registry_errors(original, REGISTRY)
    assert original == snapshot
