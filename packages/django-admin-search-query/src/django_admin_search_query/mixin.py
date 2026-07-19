"""Admin changelist mixin wiring the query language into Django admin search.

Drop :class:`SearchQueryAdminMixin` in front of ``admin.ModelAdmin`` and the
changelist search box accepts the structured query language. Anything that is
not a valid query -- including a plain word -- degrades to Django's built-in
``search_fields`` behavior, so the box never gets worse than stock admin.
"""

from __future__ import annotations

import logging
import typing as t

from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.urls import path, reverse

from django_search_query import QueryParseError, search_query_to_q
from django_search_query.highlight import apply_registry_errors, highlight_query_spans

if t.TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from django.contrib.admin import ModelAdmin
    from django.db.models import Model, QuerySet
    from django.http import HttpRequest, HttpResponse
    from django.urls import URLPattern

    from django_search_query.registry import FieldRegistry, FieldSpec

    # At type-check time the mixin is a ModelAdmin so ``super()`` resolves and
    # ``self`` carries the admin API; at runtime it is a plain mixin (object).
    _Base = ModelAdmin[Model]
else:
    _Base = object

logger = logging.getLogger(__name__)


def _strip_search_field_prefixes(search_fields: Iterable[str]) -> tuple[str, ...]:
    """Strip Django ``search_fields`` lookup sigils (``^``, ``=``, ``@``, ``$``)."""
    return tuple(field.lstrip("^=@$") for field in search_fields)


def _operators_for_spec(spec: FieldSpec) -> list[str]:
    """Return the operator tokens a field accepts, for autocomplete hints.

    Comparison-capable fields expose ``>``/``>=``/``<``/``<=``; range-capable
    fields expose the ``[`` and ``{`` range openers.
    """
    operators: list[str] = []
    if spec.supports_comparison:
        operators += [">", ">=", "<", "<="]
    if spec.supports_range:
        operators += ["[", "{"]
    return operators


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

    # A per-admin changelist template (extending stock admin) renders the
    # search box with the token/highlight endpoint URLs as ``data-*`` hooks and
    # pulls in the assets below. Scoping it to this template keeps every other
    # admin's search box untouched.
    change_list_template = "django_admin_search_query/change_list.html"

    class Media:
        """Assets that progressively enhance the changelist search box."""

        js = ("django_admin_search_query/search-input.js",)
        css = {"all": ("django_admin_search_query/search-input.css",)}  # noqa: RUF012

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

    # -- Colored-input endpoints ------------------------------------------

    def get_urls(self) -> list[URLPattern]:
        """Prepend the token and highlight endpoints to the admin URLs.

        The extra paths are prepended, not appended: the admin's trailing
        ``<path:object_id>`` catch-all would otherwise capture
        ``search-tokens``/``search-highlight`` and 302-redirect them to the
        change view. Each view is wrapped in ``admin_site.admin_view`` so it
        inherits the admin's staff-login gate.
        """
        app_label, model_name = self.opts.app_label, self.opts.model_name
        extra = [
            path(
                "search-tokens/",
                self.admin_site.admin_view(self.search_tokens_view),
                name=f"{app_label}_{model_name}_search_tokens",
            ),
            path(
                "search-highlight/",
                self.admin_site.admin_view(self.search_highlight_view),
                name=f"{app_label}_{model_name}_search_highlight",
            ),
        ]
        return extra + super().get_urls()

    def search_tokens_view(self, request: HttpRequest) -> HttpResponse:
        """Return the registry's fields and defaults as autocomplete JSON.

        Emits one entry per field (``name``, ``kind``, ``operators``,
        ``enum_values``, ``aliases``) plus the default search fields, so the
        JS autocomplete can suggest field names and enum values without a JS
        copy of the schema.
        """
        if not self.has_view_permission(request):
            raise PermissionDenied
        registry = self.get_search_query_registry()
        fields = (
            [
                {
                    "name": spec.name,
                    "kind": spec.kind,
                    "operators": _operators_for_spec(spec),
                    "enum_values": list(spec.enum_values),
                    "aliases": list(spec.aliases),
                }
                for spec in registry.specs
            ]
            if registry is not None
            else []
        )
        return JsonResponse(
            {
                "fields": fields,
                "default_fields": list(self.get_search_query_default_fields()),
            },
        )

    def search_highlight_view(self, request: HttpRequest) -> HttpResponse:
        """Return registry-aware highlight spans for ``?q=`` as JSON.

        The single source of truth for the colored input: the server lexes the
        query with :func:`~django_search_query.highlight.highlight_query_spans`
        and upgrades registry-rejected fields/values to the ``error`` role, so
        the JS renders exactly what the Python engine sees -- no client-side
        tokenizer to drift.
        """
        if not self.has_view_permission(request):
            raise PermissionDenied
        query = request.GET.get("q", "")
        logger.debug(
            "highlight requested",
            extra={"django_search_query_len": len(query)},
        )
        spans = highlight_query_spans(query)
        registry = self.get_search_query_registry()
        if registry is not None:
            spans = apply_registry_errors(spans, registry)
        return JsonResponse(
            {
                "query": query,
                "spans": [
                    {"start": span.start, "role": span.role, "text": span.text}
                    for span in spans
                ],
            },
        )

    def changelist_view(
        self,
        request: HttpRequest,
        extra_context: dict[str, t.Any] | None = None,
    ) -> HttpResponse:
        """Inject the endpoint URLs so the template can render ``data-*`` hooks.

        Reversing here (rather than in the template) keeps the model-scoped URL
        names -- ``<app>_<model>_search_tokens`` / ``..._search_highlight`` --
        out of the template, which only sees two ready-made URL strings.
        """
        app_label, model_name = self.opts.app_label, self.opts.model_name
        current_app = self.admin_site.name
        context = {
            **(extra_context or {}),
            "search_tokens_url": reverse(
                f"admin:{app_label}_{model_name}_search_tokens",
                current_app=current_app,
            ),
            "search_highlight_url": reverse(
                f"admin:{app_label}_{model_name}_search_highlight",
                current_app=current_app,
            ),
        }
        return super().changelist_view(request, context)


__all__ = ["SearchQueryAdminMixin"]
