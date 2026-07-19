"""Whole-string, never-raising lexer for query-syntax highlighting.

This is a *presentation* lexer, distinct from
:func:`~django_search_query.tokenizer.tokenize`. The tokenizer drops
whitespace, normalizes quoted phrases, and raises
:class:`~django_search_query.errors.QueryParseError` on malformed input --
all wrong for a live search box, where a half-typed query must still colorize
character-for-character. :func:`highlight_query_spans` instead runs a single
named-group regex over the *entire* string (including whitespace and
unterminated quotes) and always succeeds, thanks to a trailing catch-all.

The emitted ``(start, role, text)`` spans cover the source end to end, in
order, so a consumer can rebuild the string or stylize by offset. Roles are the
vocabulary in :data:`HIGHLIGHT_ROLES`; each frontend maps them to its own
styling. :func:`apply_registry_errors` is a second pass that upgrades ``field``
and ``value`` spans to the ``error`` role when a :class:`FieldRegistry`
rejects them (unknown field, or an out-of-enum value), so a server-side
highlighter can flag mistakes the plain lexer cannot see.
"""

from __future__ import annotations

import re
import typing as t

if t.TYPE_CHECKING:
    from django_search_query.registry import FieldRegistry


class Span(t.NamedTuple):
    """One contiguous highlight span with its source offset.

    Parameters
    ----------
    start : int
        Zero-based offset of the span in the source query.
    role : str
        One of :data:`HIGHLIGHT_ROLES`.
    text : str
        The exact source substring the span covers.
    """

    start: int
    role: str
    text: str


HIGHLIGHT_ROLES: frozenset[str] = frozenset(
    {
        "whitespace",
        "field",
        "punct",
        "keyword",
        "negation",
        "operator",
        "wildcard",
        "phrase",
        "value",
        "error",
    },
)
"""Every role :func:`highlight_query_spans` and :func:`apply_registry_errors` emit.

``error`` is never produced by the plain lexer; only
:func:`apply_registry_errors` promotes a span to it.
"""

# One pass over the whole query. Order matters: the most specific alternative
# that can start at a position must come first. Every position is covered --
# ``whitespace`` absorbs runs of blanks/newlines and ``misc`` is a single-char
# catch-all -- so ``finditer`` yields gap-free, contiguous spans and never
# rejects a character (the guarantee the live search box relies on).
_TOKEN_RE = re.compile(
    r"""
      (?P<whitespace>\s+)
    | (?P<phrase>"(?:\\.|[^"\\])*"?|'(?:\\.|[^'\\])*'?)
    | (?P<field>[A-Za-z_][A-Za-z0-9_]*)(?=:)
    | (?P<keyword>(?:AND|OR|NOT|TO)(?![\w]))
    | (?P<operator>>=|<=|[<>])
    | (?P<punct>[:()\[\]{}])
    | (?P<negation>(?<![^\s([{])[-+])
    | (?P<wildcard>[*?])
    | (?P<value>[^\s:()\[\]{}<>*?"'+]+)
    | (?P<misc>.)
    """,
    re.VERBOSE,
)

# ``misc`` (an unclassifiable single char) reads as a value so a stray symbol
# still colors like the term it sits in rather than vanishing.
_MISC_ROLE = "value"


def highlight_query_spans(query: str) -> list[Span]:
    """Lex ``query`` into contiguous ``(start, role, text)`` highlight spans.

    Never raises: malformed input (an unterminated quote, a lone bracket)
    still yields a full, gap-free span list so a live editor can colorize an
    in-progress query character-for-character.

    Parameters
    ----------
    query : str
        The raw search string, exactly as typed.

    Returns
    -------
    list[Span]
        Spans in source order whose ``text`` fields concatenate back to
        ``query``.

    Examples
    --------
    >>> highlight_query_spans("status:open")
    [Span(start=0, role='field', text='status'), Span(start=6, role='punct', \
text=':'), Span(start=7, role='value', text='open')]
    >>> [s.role for s in highlight_query_spans("a OR b")]
    ['value', 'whitespace', 'keyword', 'whitespace', 'value']
    >>> [s.role for s in highlight_query_spans('-draft "half')]
    ['negation', 'value', 'whitespace', 'phrase']
    >>> "".join(s.text for s in highlight_query_spans("created:>2024-01-01"))
    'created:>2024-01-01'
    """
    spans: list[Span] = []
    for match in _TOKEN_RE.finditer(query):
        group = match.lastgroup or "misc"
        role = _MISC_ROLE if group == "misc" else group
        spans.append(Span(match.start(), role, match.group()))
    return spans


def apply_registry_errors(
    spans: t.Sequence[Span],
    registry: FieldRegistry,
) -> list[Span]:
    """Return ``spans`` with registry-rejected fields and values re-roled ``error``.

    A second pass over the lexer output that the plain lexer cannot do alone:
    it consults ``registry`` to flag an unknown field (both the ``field`` span
    and its value are re-roled ``error``) and an out-of-enum value (only the
    ``value`` span). Spans the registry accepts are returned unchanged.

    Parameters
    ----------
    spans : Sequence[Span]
        Output of :func:`highlight_query_spans`.
    registry : FieldRegistry
        Field schema the values are validated against.

    Returns
    -------
    list[Span]
        A new list; inputs are never mutated.

    Examples
    --------
    >>> from django_search_query.registry import FieldRegistry, FieldSpec
    >>> reg = FieldRegistry(
    ...     specs=(FieldSpec(name="status", kind="enum",
    ...                      enum_values=("open", "draft")),),
    ... )
    >>> [s.role for s in apply_registry_errors(
    ...     highlight_query_spans("status:bogus"), reg)]
    ['field', 'punct', 'error']
    >>> [s.role for s in apply_registry_errors(
    ...     highlight_query_spans("author:tony"), reg)]
    ['error', 'punct', 'error']
    """
    result = list(spans)
    for index, span in enumerate(result):
        if span.role != "field":
            continue
        spec = registry.get(span.text)
        value_index = _value_index_after_field(result, index)
        if spec is None:
            result[index] = span._replace(role="error")
            if value_index is not None:
                result[value_index] = result[value_index]._replace(role="error")
            continue
        if spec.kind == "enum" and spec.enum_values and value_index is not None:
            value = result[value_index]
            if value.role == "value" and value.text not in spec.enum_values:
                result[value_index] = value._replace(role="error")
    return result


def _value_index_after_field(spans: list[Span], field_index: int) -> int | None:
    """Return the index of the value span for the field at ``field_index``.

    A field predicate lexes as ``field`` ``:`` ``value`` in three consecutive
    spans; this returns the value's index, or ``None`` when the field is not
    immediately followed by ``: value`` (e.g. a comparison or a range, which
    carry no enum to validate).
    """
    colon_index = field_index + 1
    value_index = field_index + 2
    if value_index >= len(spans):
        return None
    colon = spans[colon_index]
    if colon.role != "punct" or colon.text != ":":
        return None
    if spans[value_index].role in {"value", "phrase"}:
        return value_index
    return None


__all__ = [
    "HIGHLIGHT_ROLES",
    "Span",
    "apply_registry_errors",
    "highlight_query_spans",
]
