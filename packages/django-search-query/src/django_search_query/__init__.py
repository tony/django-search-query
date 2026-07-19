"""django-search-query: a reusable search query language for Django.

The package accepts a structured, human-friendly search string and translates
it into Django-compatible query behavior, giving applications a consistent
search syntax without prescribing a particular user interface, admin
integration, or search backend.

The syntax draws on Lucene -- field-scoped terms, quoted phrases, boolean
operators (``AND``/``OR``/``NOT``), grouping, comparisons, and ranges -- but
does not claim full Lucene compatibility.

Public flow: :func:`~django_search_query.parser.parse` turns a string into an
AST; :func:`~django_search_query.compiler.build_q` lowers the AST into a
Django ``Q``. :func:`search_query_to_q` chains both for the common case.
"""

from __future__ import annotations

import logging
import typing as t

from .__about__ import __version__
from .compiler import build_q
from .errors import QueryParseError
from .parser import parse

if t.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from django.db.models import Q

    from .registry import FieldRegistry

# Library code must never configure logging handlers, levels, or formatters
# -- that is the consuming application's job. A NullHandler keeps Python from
# emitting "No handlers could be found" warnings when the app stays silent.
logging.getLogger(__name__).addHandler(logging.NullHandler())


def search_query_to_q(
    query: str,
    *,
    registry: FieldRegistry,
    field_map: Mapping[str, str],
    default_fields: Sequence[str],
) -> Q:
    """Parse ``query`` and compile it to a Django ``Q`` in one call.

    Parameters
    ----------
    query : str
        The user-supplied search string.
    registry : FieldRegistry
        Field schema used to validate field names.
    field_map : Mapping[str, str]
        Maps canonical field names to ORM lookup paths.
    default_fields : Sequence[str]
        ORM paths searched for bare terms and phrases.

    Returns
    -------
    Q
        The compiled query.

    Raises
    ------
    QueryParseError
        If ``query`` cannot be parsed.

    Examples
    --------
    >>> from django_search_query.registry import FieldRegistry, FieldSpec
    >>> reg = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
    >>> search_query_to_q(
    ...     "status:open", registry=reg, field_map={"status": "status"},
    ...     default_fields=("title",),
    ... )
    <Q: (AND: ('status__iexact', 'open'))>
    """
    # FieldSpec.path is the authoritative ORM path; the caller's field_map
    # overrides it per-call. Merge so an unmapped field still resolves to its
    # registered path rather than its bare name.
    resolved_map = {spec.name: spec.path for spec in registry.specs}
    resolved_map.update(field_map)
    return build_q(
        parse(query, registry),
        resolved_map,
        default_fields=default_fields,
    )


__all__ = [
    "QueryParseError",
    "__version__",
    "build_q",
    "parse",
    "search_query_to_q",
]
