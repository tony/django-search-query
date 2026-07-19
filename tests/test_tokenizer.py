"""Tests for the hand-written tokenizer."""

from __future__ import annotations

import pytest

from django_search_query.errors import QueryParseError
from django_search_query.tokenizer import tokenize


def _kinds(query: str) -> list[str]:
    """Return the token kinds for ``query`` (dropping the trailing eof)."""
    return [tok.kind for tok in tokenize(query)[:-1]]


def test_field_value_split() -> None:
    """A ``field:value`` word lexes into ident, colon, and term."""
    tokens = tokenize("status:open")
    assert _kinds("status:open") == ["ident", "colon", "term"]
    assert tokens[0].value == "status"
    assert tokens[2].value == "open"


def test_offsets_are_preserved() -> None:
    """Each token records its start offset in the source string."""
    tokens = tokenize("a  bee")
    assert tokens[0].start == 0
    assert tokens[1].start == 3


def test_quoted_phrase_collapses_whitespace() -> None:
    """A quoted phrase becomes one ``term`` with collapsed whitespace."""
    (token, _eof) = tokenize('"deploy   v1"')
    assert token.kind == "term"
    assert token.is_phrase is True
    assert token.value == "deploy v1"


def test_comparison_and_range_punctuation() -> None:
    """Comparison operators and range brackets each lex to their own kind."""
    assert _kinds("created:>=2024") == ["ident", "colon", "gte", "term"]
    assert _kinds("n:[1 TO 5]") == [
        "ident",
        "colon",
        "lbracket",
        "term",
        "to",
        "term",
        "rbracket",
    ]


def test_keywords_and_sigils() -> None:
    """Boolean keywords and leading sigils lex to operator kinds."""
    assert _kinds("a AND b OR NOT c") == [
        "term",
        "and",
        "term",
        "or",
        "not",
        "term",
    ]
    assert _kinds("-a +b") == ["minus", "term", "plus", "term"]


def test_hyphen_inside_word_is_not_a_sigil() -> None:
    """A ``-`` mid-word stays part of the term, not a NOT sigil."""
    assert _kinds("multi-word") == ["term"]
    assert tokenize("multi-word")[0].value == "multi-word"


def test_unterminated_quote_raises_positioned_error() -> None:
    """An unterminated quote raises a positioned ``QueryParseError``."""
    with pytest.raises(QueryParseError) as excinfo:
        tokenize('"open')
    assert excinfo.value.position == 0


def test_stream_ends_with_eof() -> None:
    """Every token stream terminates with a synthetic eof marker."""
    tokens = tokenize("x")
    assert tokens[-1].kind == "eof"
    assert tokens[-1].start == 1
