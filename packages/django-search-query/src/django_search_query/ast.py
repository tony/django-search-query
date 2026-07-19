"""Frozen AST nodes shared by the parser and the compiler.

Nodes are ``frozen``, ``slots`` dataclasses so a parsed tree is immutable and
cheap. The parser produces them; :mod:`django_search_query.compiler` consumes
them with structural ``match``. The :data:`Node` union (PEP 695 ``type``
alias) names every shape either side may encounter.
"""

from __future__ import annotations

import dataclasses
import typing as t

from django_search_query.registry import FieldKind

CmpOp = t.Literal["gt", "gte", "lt", "lte"]
"""Comparison operator carried by :class:`Cmp` and the parser's op table."""


@dataclasses.dataclass(slots=True, frozen=True)
class Term:
    """A bare positional term, e.g. ``bliss`` or the phrase ``"a b"``.

    Parameters
    ----------
    value : str
        The term text (unquoted for phrases).
    is_phrase : bool
        Whether the term came from a quoted phrase.
    """

    value: str
    is_phrase: bool = False


@dataclasses.dataclass(slots=True, frozen=True)
class Field:
    """A ``field:value`` predicate.

    Parameters
    ----------
    field : str
        Canonical field name (aliases already resolved).
    value : str
        Raw value text; the compiler applies wildcard rules.
    kind : FieldKind
        Field kind carried from the registry so the compiler can pick
        ``iexact`` (enum) versus ``icontains`` (string) without a second
        registry lookup.
    """

    field: str
    value: str
    kind: FieldKind = "string"


@dataclasses.dataclass(slots=True, frozen=True)
class Cmp:
    """A ``field:>value`` style comparison predicate.

    Parameters
    ----------
    field : str
        Canonical field name.
    op : {"gt", "gte", "lt", "lte"}
        Comparison operator.
    value : str
        Right-hand value (kept as source text for v1).
    """

    field: str
    op: CmpOp
    value: str


@dataclasses.dataclass(slots=True, frozen=True)
class Range:
    """A ``field:[a TO b]`` / ``field:{a TO b}`` predicate.

    Parameters
    ----------
    field : str
        Canonical field name.
    lo, hi : str
        Bounds; the literal ``*`` omits that side.
    inclusive_lo, inclusive_hi : bool
        Whether each bound is inclusive (``[`` / ``]``) or exclusive
        (``{`` / ``}``).
    """

    field: str
    lo: str
    hi: str
    inclusive_lo: bool
    inclusive_hi: bool


@dataclasses.dataclass(slots=True, frozen=True)
class Exists:
    """A ``field:*`` predicate: the field is present and non-empty.

    Parameters
    ----------
    field : str
        Canonical field name.
    """

    field: str


@dataclasses.dataclass(slots=True, frozen=True)
class Not:
    """Boolean negation of a child node.

    Parameters
    ----------
    child : Node
        The negated sub-expression.
    """

    child: Node


@dataclasses.dataclass(slots=True, frozen=True)
class And:
    """N-ary conjunction of two or more children.

    Parameters
    ----------
    children : tuple[Node, ...]
        Operands joined by ``AND`` (explicit or implicit).
    """

    children: tuple[Node, ...]


@dataclasses.dataclass(slots=True, frozen=True)
class Or:
    """N-ary disjunction of two or more children.

    Parameters
    ----------
    children : tuple[Node, ...]
        Operands joined by ``OR``.
    """

    children: tuple[Node, ...]


type Node = Term | Field | Cmp | Range | Exists | Not | And | Or
"""Every AST shape the parser may emit or the compiler may consume."""


__all__ = [
    "And",
    "Cmp",
    "CmpOp",
    "Exists",
    "Field",
    "Node",
    "Not",
    "Or",
    "Range",
    "Term",
]
