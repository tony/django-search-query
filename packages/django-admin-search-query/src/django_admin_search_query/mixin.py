"""Admin changelist mixin wiring the query language into Django admin search.

Drop :class:`SearchQueryAdminMixin` in front of ``admin.ModelAdmin`` and the
changelist search box accepts the structured query language. Anything that is
not a valid query -- including a plain word -- degrades to Django's built-in
``search_fields`` behavior, so the box never gets worse than stock admin.
"""

from __future__ import annotations

import logging
import typing as t

from django_search_query import QueryParseError, search_query_to_q

if t.TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from django.contrib.admin import ModelAdmin
    from django.db.models import Model, QuerySet
    from django.http import HttpRequest

    from django_search_query.registry import FieldRegistry

    # At type-check time the mixin is a ModelAdmin so ``super()`` resolves and
    # ``self`` carries the admin API; at runtime it is a plain mixin (object).
    _Base = ModelAdmin[Model]
else:
    _Base = object

logger = logging.getLogger(__name__)


def _strip_search_field_prefixes(search_fields: Iterable[str]) -> tuple[str, ...]:
    """Strip Django ``search_fields`` lookup sigils (``^``, ``=``, ``@``, ``$``)."""
    return tuple(field.lstrip("^=@$") for field in search_fields)


class SearchQueryAdminMixin(_Base):
    """Parse the changelist search box with the structured query language.

    Subclasses configure the language via three class attributes (or override
    the matching ``get_*`` hooks for dynamic behavior):

    - ``search_query_registry`` -- the :class:`FieldRegistry` to validate
      against (required for field-scoped queries to resolve).
    - ``search_query_field_map`` -- maps field names to ORM lookup paths.
    - ``search_query_default_fields`` -- ORM paths bare terms search; falls
      back to the admin's ``search_fields`` when unset.
    """

    search_query_registry: t.ClassVar[FieldRegistry | None] = None
    search_query_field_map: t.ClassVar[Mapping[str, str]] = {}
    search_query_default_fields: t.ClassVar[Sequence[str]] = ()

    def get_search_query_registry(self) -> FieldRegistry | None:
        """Return the registry used to validate field names."""
        return self.search_query_registry

    def get_search_query_field_map(self) -> Mapping[str, str]:
        """Return the field-name to ORM-path mapping."""
        return self.search_query_field_map

    def get_search_query_default_fields(self) -> Sequence[str]:
        """Return ORM paths for bare terms, defaulting to ``search_fields``.

        Django ``search_fields`` may carry lookup-prefix sigils (``^`` / ``=``
        / ``@`` / ``$``); strip them so bare-term ``icontains`` lookups stay
        valid.
        """
        if self.search_query_default_fields:
            return self.search_query_default_fields
        return _strip_search_field_prefixes(self.search_fields)

    def get_search_results(
        self,
        request: HttpRequest,
        queryset: QuerySet[t.Any],
        search_term: str,
    ) -> tuple[QuerySet[t.Any], bool]:
        """Filter ``queryset`` by parsing ``search_term`` as a query.

        Empty terms and unparseable terms fall back to Django's default
        search so behavior never regresses below stock admin.

        Parameters
        ----------
        request : HttpRequest
            The changelist request.
        queryset : QuerySet
            The base changelist queryset.
        search_term : str
            The raw contents of the admin search box.

        Returns
        -------
        tuple[QuerySet, bool]
            The filtered queryset and whether duplicates may result (always
            ``False`` here: ``Q`` filtering introduces no joins that Django's
            distinct handling needs to know about).
        """
        term = search_term.strip()
        registry = self.get_search_query_registry()
        if not term or registry is None:
            return super().get_search_results(request, queryset, search_term)
        try:
            query = search_query_to_q(
                term,
                registry=registry,
                field_map=self.get_search_query_field_map(),
                default_fields=self.get_search_query_default_fields(),
            )
        except QueryParseError:
            logger.debug(
                "query parse failed; falling back to default search",
                extra={"django_search_query_len": len(term)},
            )
            return super().get_search_results(request, queryset, search_term)
        return queryset.filter(query), False


__all__ = ["SearchQueryAdminMixin"]
