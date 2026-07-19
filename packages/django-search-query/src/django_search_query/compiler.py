"""Lower a parsed AST into a Django :class:`~django.db.models.Q` object.

The compiler is a single structural ``match`` over :data:`Node`. It is kept
separate from the parser so the AST stays a stable contract: the parser owns
syntax and field validation, the compiler owns the ORM mapping (which lookup,
which path). Field names resolve to ORM paths through a caller-supplied
``field_map`` (defaulting to the name itself when unmapped).
"""

from __future__ import annotations

import logging
import typing as t

from django.db.models import Q

from django_search_query.ast import (
    And,
    Cmp,
    Exists,
    Field,
    Node,
    Not,
    Or,
    Range,
    Term,
)

if t.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

logger = logging.getLogger(__name__)


def build_q(
    node: Node,
    field_map: Mapping[str, str],
    *,
    default_fields: Sequence[str],
) -> Q:
    """Compile ``node`` into a Django ``Q`` object.

    Parameters
    ----------
    node : Node
        Root of a parsed AST.
    field_map : Mapping[str, str]
        Maps canonical field names to ORM lookup paths. Unmapped names fall
        back to themselves.
    default_fields : Sequence[str]
        ORM paths searched (OR-ed) for bare terms and phrases.

    Returns
    -------
    Q
        The compiled query, ready for ``queryset.filter``.

    Examples
    --------
    >>> from django_search_query.ast import Term
    >>> build_q(Term(value="hi"), {}, default_fields=("title",))
    <Q: (AND: ('title__icontains', 'hi'))>
    >>> from django_search_query.ast import Field
    >>> build_q(Field("status", "open", "enum"), {"status": "state"},
    ...         default_fields=())
    <Q: (AND: ('state__iexact', 'open'))>
    """
    match node:
        case Term(value=value, is_phrase=is_phrase):
            return _text_q(value, default_fields, phrase=is_phrase)
        case Field(field=field, value=value, kind=kind):
            path = field_map.get(field, field)
            if kind == "enum":
                return Q(**{f"{path}__iexact": value})
            return _wildcard_q(path, value)
        case Cmp(field=field, op=op, value=value):
            path = field_map.get(field, field)
            return Q(**{f"{path}__{op}": value})
        case Range(field=field, lo=lo, hi=hi, inclusive_lo=inc_lo, inclusive_hi=inc_hi):
            path = field_map.get(field, field)
            query = Q()
            if lo != "*":
                query &= Q(**{f"{path}__{'gte' if inc_lo else 'gt'}": lo})
            if hi != "*":
                query &= Q(**{f"{path}__{'lte' if inc_hi else 'lt'}": hi})
            return query
        case Exists(field=field):
            path = field_map.get(field, field)
            return ~Q(**{path: ""}) & ~Q(**{f"{path}__isnull": True})
        case Not(child=child):
            return ~build_q(child, field_map, default_fields=default_fields)
        case And(children=children):
            query = Q()
            for child in children:
                query &= build_q(child, field_map, default_fields=default_fields)
            return query
        case Or(children=children):
            query = Q()
            for child in children:
                query |= build_q(child, field_map, default_fields=default_fields)
            return query
    t.assert_never(node)


def _text_q(value: str, default_fields: Sequence[str], *, phrase: bool) -> Q:
    """OR a term or phrase across ``default_fields``.

    Phrases match verbatim with ``icontains``; bare terms honor wildcard
    rules (``foo*`` -> ``istartswith``, ``*foo`` -> ``iendswith``).
    """
    lookup, term = ("icontains", value) if phrase else _wildcard_lookup(value)
    query = Q()
    for field in default_fields:
        query |= Q(**{f"{field}__{lookup}": term})
    return query


def _wildcard_q(path: str, value: str) -> Q:
    """Compile a single ``field:value`` predicate with wildcard rules."""
    lookup, term = _wildcard_lookup(value)
    return Q(**{f"{path}__{lookup}": term})


def _wildcard_lookup(value: str) -> tuple[str, str]:
    """Return the ``(lookup, term)`` pair implied by any ``*`` wildcards.

    ``foo*`` anchors the start (``istartswith``), ``*foo`` the end
    (``iendswith``); a bare or doubly-wrapped value uses ``icontains``.
    """
    star_lead = value.startswith("*")
    star_tail = value.endswith("*")
    if star_lead and star_tail:
        return "icontains", value.strip("*")
    if star_tail:
        return "istartswith", value[:-1]
    if star_lead:
        return "iendswith", value[1:]
    return "icontains", value


__all__ = ["build_q"]
