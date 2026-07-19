"""Pygments lexer for the django-search-query query language.

Used by the docs so ``dsq`` code fences highlight under whatever Pygments
style the theme selects, matching the rest of the documentation's code blocks
in light and dark mode.

The lexer reuses :func:`~django_search_query.highlight.highlight_query_spans`
-- the same presentation grammar the live search box highlights with -- and
maps each role to a standard Pygments token type, so the surfaces never drift.
It is a docs/test-time helper, never imported by the runtime, so
:mod:`pygments` is not a runtime dependency.
"""

from __future__ import annotations

import typing as t

from pygments.lexer import Lexer
from pygments.token import (
    Error,
    Keyword,
    Name,
    Operator,
    Punctuation,
    String,
    Text,
)

from django_search_query.highlight import highlight_query_spans

if t.TYPE_CHECKING:
    import collections.abc as cabc

    from pygments.token import _TokenType

__all__ = ["DjangoSearchQueryLexer"]

# Highlight role -> standard Pygments token. Standard tokens keep the docs
# themeable: the active Pygments style colors them and adapts to light/dark.
_ROLE_TOKENS: dict[str, _TokenType] = {
    "whitespace": Text.Whitespace,
    "field": Name.Attribute,
    "punct": Punctuation,
    "keyword": Keyword,
    "negation": Operator,
    "operator": Operator,
    "wildcard": Operator,
    "phrase": String.Double,
    "value": Text,
    "error": Error,
}


class DjangoSearchQueryLexer(Lexer):
    """Highlight query syntax (``status:open "exact phrase"``)."""

    # Pygments' ``Lexer`` declares these as plain attributes, so they are
    # matched here rather than annotated ``ClassVar`` (which ty would flag).
    name = "django-search-query"
    aliases = ["dsq"]  # noqa: RUF012 -- matches Pygments Lexer base
    url = "https://django-search-query.git-pull.com"

    def get_tokens_unprocessed(
        self,
        text: str,
    ) -> cabc.Iterator[tuple[int, _TokenType, str]]:
        """Yield ``(index, token_type, value)`` for each query span.

        Delegates to
        :func:`~django_search_query.highlight.highlight_query_spans` so token
        boundaries match the live search box exactly.

        Examples
        --------
        >>> lexer = DjangoSearchQueryLexer()
        >>> [(str(tok), val)
        ...  for _, tok, val in lexer.get_tokens_unprocessed("status:open")]
        [('Token.Name.Attribute', 'status'), ('Token.Punctuation', ':'),
         ('Token.Text', 'open')]
        """
        for start, role, value in highlight_query_spans(text):
            yield start, _ROLE_TOKENS.get(role, Text), value
