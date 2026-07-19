"""Precedence-climbing (Pratt) parser for the search query language.

Rather than one method per precedence level, a single :meth:`_Parser._expr`
loop is driven by binding-power tables. Every token has a *null denotation*
(``nud`` -- how it starts an expression: term, field, group, or a ``NOT`` /
``-`` / ``+`` prefix) and, for operators, a *left binding power* (``lbp`` --
how tightly it binds the expression to its left).

Binding powers (higher binds tighter)::

    OR                10   infix, left-associative
    AND / implicit    20   infix, left-associative (juxtaposition == AND)
    NOT / - / +       30   prefix

Because ``NOT`` binds at 30 while ``AND`` binds at 20, ``NOT a AND b`` parses
as ``(NOT a) AND b``. Adjacent primaries (``a b``) are treated as an implicit
``AND`` operator sharing ``AND``'s binding power, so precedence between
implicit and explicit conjunction is uniform. Grouping is just a primary that
recurses at the lowest binding power.

Grammar (the precedence-climbing loop realizes this; a JavaScript
re-implementation for the search input can mirror it 1:1)::

    query       := expr
    expr        := prefix (infix prefix)*
    infix       := "OR" | "AND" | <juxtaposition>   # juxtaposition == AND
    prefix      := ("NOT" | "-" | "+")? primary
    primary     := "(" expr ")" | field | term
    field       := IDENT ":" (comparison | range | value | "*")
    comparison  := (">" | ">=" | "<" | "<=") TERM
    range       := ("[" | "{") TERM "TO" TERM ("]" | "}")
    value       := TERM
    term        := TERM | PHRASE
"""

from __future__ import annotations

import logging

from django_search_query.ast import (
    And,
    Cmp,
    CmpOp,
    Exists,
    Field,
    Node,
    Not,
    Or,
    Range,
    Term,
)
from django_search_query.errors import QueryParseError
from django_search_query.registry import FieldRegistry
from django_search_query.tokenizer import Token, TokenKind, tokenize

logger = logging.getLogger(__name__)

_OR_BP = 10
_AND_BP = 20
_NOT_BP = 30

# Tokens that can begin a primary; juxtaposition of two of them is implicit AND.
_PRIMARY_STARTS: frozenset[TokenKind] = frozenset(
    {"term", "ident", "lparen", "not", "minus", "plus"},
)

_CMP_OPS: dict[TokenKind, CmpOp] = {
    "gt": "gt",
    "lt": "lt",
    "gte": "gte",
    "lte": "lte",
}


def parse(query: str, registry: FieldRegistry) -> Node:
    """Parse ``query`` into an AST, validating fields against ``registry``.

    Parameters
    ----------
    query : str
        The user-supplied search string.
    registry : FieldRegistry
        Field schema; unknown fields raise a positioned error.

    Returns
    -------
    Node
        Root of the parsed tree. Single terms return a bare :class:`Term`
        (no one-child ``And``/``Or`` wrapper).

    Raises
    ------
    QueryParseError
        On any lexical or grammatical failure, with a ``position``.

    Examples
    --------
    >>> from django_search_query.registry import FieldRegistry, FieldSpec
    >>> reg = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
    >>> node = parse("hello world", reg)
    >>> type(node).__name__, len(node.children)
    ('And', 2)
    >>> parse("status:open", reg)
    Field(field='status', value='open', kind='enum')
    """
    logger.debug("parse started", extra={"django_search_query_len": len(query)})
    parser = _Parser(tokens=tokenize(query), registry=registry)
    node = parser._expr(0)
    parser._expect("eof")
    return node


class _Parser:
    """Cursor over a token stream driving the Pratt expression loop."""

    __slots__ = ("_pos", "registry", "tokens")

    def __init__(self, *, tokens: tuple[Token, ...], registry: FieldRegistry) -> None:
        self.tokens = tokens
        self.registry = registry
        self._pos = 0

    def _peek(self) -> Token:
        """Return the current token without advancing."""
        return self.tokens[self._pos]

    def _advance(self) -> Token:
        """Consume and return the current token."""
        token = self.tokens[self._pos]
        self._pos += 1
        return token

    def _expect(self, kind: TokenKind) -> Token:
        """Consume the current token, erroring if its kind differs."""
        token = self._peek()
        if token.kind != kind:
            message = f"expected {kind}, got {token.kind} ({token.value!r})"
            raise QueryParseError(message, position=token.start)
        return self._advance()

    def _expr(self, min_bp: int) -> Node:
        """Parse an expression whose operators bind at least ``min_bp``.

        The precedence-climbing core: parse a primary (``nud``), then absorb
        trailing infix operators (explicit or implicit ``AND``, ``OR``) whose
        binding power meets ``min_bp``.
        """
        left = self._nud()
        while True:
            token = self._peek()
            lbp = self._infix_bp(token)
            if lbp is None or lbp < min_bp:
                return left
            left = self._led(left, token)

    @staticmethod
    def _infix_bp(token: Token) -> int | None:
        """Return the left binding power of ``token`` as an infix operator.

        ``None`` means the token cannot continue the current expression (it
        closes a group/range or ends the stream).
        """
        if token.kind == "or":
            return _OR_BP
        if token.kind == "and" or token.kind in _PRIMARY_STARTS:
            return _AND_BP
        return None

    def _led(self, left: Node, token: Token) -> Node:
        """Combine ``left`` with the operator at ``token`` and its right side."""
        if token.kind == "or":
            _ = self._advance()
            return _join(Or, left, self._expr(_OR_BP + 1))
        if token.kind == "and":
            _ = self._advance()  # explicit AND; implicit AND consumes nothing
        return _join(And, left, self._expr(_AND_BP + 1))

    def _nud(self) -> Node:
        """Parse a primary: a prefix operator, group, field, or term."""
        token = self._peek()
        if token.kind in {"not", "minus"}:
            _ = self._advance()
            return Not(child=self._expr(_NOT_BP))
        if token.kind == "plus":
            # ``+`` marks a term as required; implicit AND already does that,
            # so it is a no-op -- consume it and parse the operand.
            _ = self._advance()
            return self._expr(_NOT_BP)
        if token.kind == "lparen":
            _ = self._advance()
            node = self._expr(0)
            _ = self._expect("rparen")
            return node
        if token.kind == "ident":
            return self._field()
        if token.kind == "term":
            _ = self._advance()
            return Term(value=token.value, is_phrase=token.is_phrase)
        message = f"unexpected token {token.kind} ({token.value!r})"
        raise QueryParseError(message, position=token.start)

    def _field(self) -> Node:
        """Parse ``ident : (comparison | range | value | exists)``."""
        ident = self._advance()
        spec = self.registry.get(ident.value)
        if spec is None:
            known = ", ".join(self.registry.known_names())
            message = f"unknown field {ident.value!r}; known fields: {known}"
            logger.debug("unknown field", extra={"django_search_field": ident.value})
            raise QueryParseError(message, position=ident.start)
        _ = self._expect("colon")
        token = self._peek()
        if token.kind in _CMP_OPS:
            return self._cmp(spec.name, spec.supports_comparison)
        if token.kind in {"lbracket", "lbrace"}:
            return self._range(spec.name, spec.supports_range)
        if token.kind == "term":
            _ = self._advance()
            if token.value == "*":
                return Exists(field=spec.name)
            if (
                spec.kind == "enum"
                and spec.enum_values
                and token.value not in spec.enum_values
            ):
                allowed = ", ".join(spec.enum_values)
                message = (
                    f"invalid value {token.value!r} for {spec.name!r}; "
                    f"allowed: {allowed}"
                )
                raise QueryParseError(message, position=token.start)
            return Field(field=spec.name, value=token.value, kind=spec.kind)
        message = f"expected a value after {spec.name}:, got {token.kind}"
        raise QueryParseError(message, position=token.start)

    def _cmp(self, field: str, supported: bool) -> Cmp:
        """Parse the ``> value`` tail of a comparison."""
        op_token = self._advance()
        if not supported:
            message = f"field {field!r} does not support comparison operators"
            raise QueryParseError(message, position=op_token.start)
        value = self._expect("term")
        return Cmp(field=field, op=_CMP_OPS[op_token.kind], value=value.value)

    def _range(self, field: str, supported: bool) -> Range:
        """Parse the ``[a TO b]`` / ``{a TO b}`` tail of a range."""
        open_token = self._advance()
        if not supported:
            message = f"field {field!r} does not support range queries"
            raise QueryParseError(message, position=open_token.start)
        inclusive = open_token.kind == "lbracket"
        lo = self._expect("term").value
        _ = self._expect("to")
        hi = self._expect("term").value
        _ = self._expect("rbracket" if inclusive else "rbrace")
        return Range(
            field=field,
            lo=lo,
            hi=hi,
            inclusive_lo=inclusive,
            inclusive_hi=inclusive,
        )


def _join(op: type[And] | type[Or], left: Node, right: Node) -> Node:
    """Combine ``left`` and ``right`` under ``op``, flattening same-op nests.

    Keeps ``And`` / ``Or`` n-ary so ``a b c`` yields a single ``And`` of three
    children rather than a left-leaning binary chain.
    """
    children: list[Node] = []
    for side in (left, right):
        if isinstance(side, op):
            children.extend(side.children)
        else:
            children.append(side)
    return op(children=tuple(children))


__all__ = ["parse"]
