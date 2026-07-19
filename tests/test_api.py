"""Tests for the ``search_query_to_q`` public entry point."""

from __future__ import annotations

from django.db.models import Q

from django_search_query import search_query_to_q
from django_search_query.registry import FieldRegistry, FieldSpec


def test_registry_path_is_honored_without_field_map() -> None:
    """``FieldSpec.path`` resolves the ORM path when no override is given."""
    registry = FieldRegistry(
        specs=(FieldSpec(name="author", kind="string", path="writer__name"),),
    )
    result = search_query_to_q(
        "author:tony",
        registry=registry,
        field_map={},
        default_fields=("title",),
    )
    assert result == Q(writer__name__icontains="tony")


def test_field_map_overrides_registry_path() -> None:
    """A caller ``field_map`` entry overrides the registered ``FieldSpec.path``."""
    registry = FieldRegistry(
        specs=(FieldSpec(name="author", kind="string", path="writer__name"),),
    )
    result = search_query_to_q(
        "author:tony",
        registry=registry,
        field_map={"author": "override__name"},
        default_fields=("title",),
    )
    assert result == Q(override__name__icontains="tony")


def test_empty_query_is_match_all() -> None:
    """An empty or whitespace-only query compiles to a match-all ``Q()``."""
    registry = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
    result = search_query_to_q(
        "   ",
        registry=registry,
        field_map={},
        default_fields=("title",),
    )
    assert result == Q()
