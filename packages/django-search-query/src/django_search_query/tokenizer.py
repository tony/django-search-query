"""Hand-written scanner turning a query string into a token stream.

The tokenizer is deliberately dumb: it classifies characters into tokens and
records source offsets, leaving all grammar decisions to the parser. Keeping
lexing separate makes both layers testable in isolation and lets error
messages point at exact positions.
"""

from __future__ import annotations

import dataclasses
import logging
import re
import typing as t

from django_search_query.errors import QueryParseError

logger = logging.getLogger(__name__)

TokenKind = t.Literal[
    "term",  # bare word or quoted phrase (a value)
    "ident",  # field name appearing left of ``:``
    "colon",  # the ``:`` separating a field from its value
    "minus",  # leading ``-`` shorthand for NOT
    "plus",  # leading ``+`` shorthand for required (a no-op in v1)
    "and",  # explicit ``AND`` keyword
    "or",  # explicit ``OR`` keyword
    "not",  # explicit ``NOT`` keyword
    "to",  # the ``TO`` keyword inside a range
    "lparen",  # ``(``
    "rparen",  # ``)``
    "lbracket",  # ``[`` inclusive range start
    "rbracket",  # ``]``
    "lbrace",  # ``{`` exclusive range start
    "rbrace",  # ``}``
    "gt",  # ``>``
    "lt",  # ``<``
    "gte",  # ``>=``
    "lte",  # ``<=``
    "eof",  # synthetic end-of-stream marker
]
"""Discriminator for each token shape the scanner emits."""

_KEYWORDS: dict[str, TokenKind] = {
    "AND": "and",
    "OR": "or",
    "NOT": "not",
    "TO": "to",
}

_SINGLE_CHARS: dict[str, TokenKind] = {
    "(": "lparen",
    ")": "rparen",
    "[": "lbracket",
    "]": "rbracket",
    "{": "lbrace",
    "}": "rbrace",
}

_WORD_RE = re.compile(r"[\w\-./~*?@:+]+", re.UNICODE)
"""Characters allowed in a bare term or field identifier.

Includes ``-``, ``.``, ``/``, ``~`` so hyphenated words, dates
(``2024-01-01``), and path-shaped values survive without quoting. ``:`` is
included so the ``ident:value`` split can be detected from a single match.
"""

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
"""Stricter rule for the field name on the left of a ``:``."""


@dataclasses.dataclass(slots=True, frozen=True)
class Token:
    """One lexed token with its source offset.

    Parameters
    ----------
    kind : TokenKind
        The token's classification.
    value : str
        Raw source text (unquoted, for phrases).
    start : int
        Zero-based offset of the token in the source query.
    is_phrase : bool
        Whether a ``term`` token came from a quoted phrase.
    """

    kind: TokenKind
    value: str
    start: int
    is_phrase: bool = False


def tokenize(query: str) -> tuple[Token, ...]:
    """Lex ``query`` into a tuple of tokens ending with an ``eof`` marker.

    Parameters
    ----------
    query : str
        The user-supplied search string.

    Returns
    -------
    tuple[Token, ...]
        Tokens in source order, terminated by a synthetic ``eof`` token.

    Raises
    ------
    QueryParseError
        On an unterminated quote or an unclassifiable character.

    Examples
    --------
    >>> [(t.kind, t.value) for t in tokenize("status:open")]
    [('ident', 'status'), ('colon', ':'), ('term', 'open'), ('eof', '')]
    >>> tokenize('"a b"')[0].is_phrase
    True
    """
    logger.debug(
        "tokenize started",
        extra={"django_search_query_len": len(query)},
    )
    tokens: list[Token] = []
    pos = 0
    length = len(query)
    # ``at_primary`` marks positions where a fresh primary may begin, so a
    # leading ``-``/``+`` is read as a sigil rather than word punctuation.
    at_primary = True
    while pos < length:
        char = query[pos]
        if char.isspace():
            pos += 1
            continue
        single = _SINGLE_CHARS.get(char)
        if single is not None:
            tokens.append(Token(kind=single, value=char, start=pos))
            pos += 1
            at_primary = True
            continue
        if char in {">", "<"}:
            two = pos + 1 < length and query[pos + 1] == "="
            kind: TokenKind = (
                ("gte" if char == ">" else "lte")
                if two
                else ("gt" if char == ">" else "lt")
            )
            tokens.append(
                Token(kind=kind, value=char + ("=" if two else ""), start=pos)
            )
            pos += 2 if two else 1
            at_primary = False
            continue
        if char in {"-", "+"} and at_primary:
            tokens.append(
                Token(kind="minus" if char == "-" else "plus", value=char, start=pos),
            )
            pos += 1
            at_primary = True
            continue
        if char in {'"', "'"}:
            value, end = _read_quoted(query, pos)
            tokens.append(Token(kind="term", value=value, start=pos, is_phrase=True))
            pos = end
            at_primary = True
            continue
        match = _WORD_RE.match(query, pos)
        if match is None:
            message = f"unexpected character {char!r}"
            raise QueryParseError(message, position=pos)
        pos = _emit_word(tokens, match.group(0), pos)
        at_primary = True
    tokens.append(Token(kind="eof", value="", start=length))
    return tuple(tokens)


def _emit_word(tokens: list[Token], raw: str, start: int) -> int:
    """Emit tokens for a bare word and return the offset past it.

    A word is one of three things: an ``ident:value`` field prefix, a
    boolean keyword, or a plain term.
    """
    colon_index = raw.find(":")
    if colon_index > 0 and _IDENT_RE.fullmatch(raw[:colon_index]):
        tokens.append(Token(kind="ident", value=raw[:colon_index], start=start))
        tokens.append(Token(kind="colon", value=":", start=start + colon_index))
        remainder = raw[colon_index + 1 :]
        if remainder:
            tokens.append(
                Token(kind="term", value=remainder, start=start + colon_index + 1),
            )
        return start + len(raw)
    # Keywords are case-sensitive (uppercase only), matching Lucene: a
    # lowercase ``and``/``or`` is a search term, not an operator, so
    # ``cats and dogs`` searches for three words rather than ``cats AND dogs``.
    keyword = _KEYWORDS.get(raw)
    if keyword is not None:
        tokens.append(Token(kind=keyword, value=raw, start=start))
        return start + len(raw)
    tokens.append(Token(kind="term", value=raw, start=start))
    return start + len(raw)


def _read_quoted(query: str, start: int) -> tuple[str, int]:
    """Read a quoted phrase beginning at ``query[start]``.

    Backslash escapes the quote and the backslash itself. Internal
    whitespace is collapsed so the phrase matches as one substring.
    Returns the unquoted value and the offset past the closing quote.
    """
    quote = query[start]
    buffer: list[str] = []
    pos = start + 1
    length = len(query)
    while pos < length:
        char = query[pos]
        if char == "\\" and pos + 1 < length:
            buffer.append(query[pos + 1])
            pos += 2
            continue
        if char == quote:
            return " ".join("".join(buffer).split()), pos + 1
        buffer.append(char)
        pos += 1
    message = f"unterminated {quote} quoted string"
    raise QueryParseError(message, position=start)


__all__ = ["Token", "TokenKind", "tokenize"]
