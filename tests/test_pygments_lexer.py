"""Tests for the query-language Pygments lexer."""

from __future__ import annotations

from pygments.token import Name, Punctuation, Text

from django_search_query.highlight import HIGHLIGHT_ROLES
from django_search_query.pygments_lexer import _ROLE_TOKENS, DjangoSearchQueryLexer


def test_every_highlight_role_has_a_token() -> None:
    """No role can fall through to the Text default silently."""
    assert set(_ROLE_TOKENS) >= HIGHLIGHT_ROLES


def test_tokens_reconstruct_the_input() -> None:
    """The lexer is gap-free: values concatenate back to the source."""
    lexer = DjangoSearchQueryLexer()
    query = "status:open OR author:tony -draft"
    rebuilt = "".join(value for _, _, value in lexer.get_tokens_unprocessed(query))
    assert rebuilt == query


def test_field_predicate_token_sequence() -> None:
    """A field predicate lexes as field, punct, value tokens in order."""
    lexer = DjangoSearchQueryLexer()
    tokens = [(tok, val) for _, tok, val in lexer.get_tokens_unprocessed("status:open")]
    assert tokens == [(Name.Attribute, "status"), (Punctuation, ":"), (Text, "open")]
