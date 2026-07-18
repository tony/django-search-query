"""Smoke tests confirming both workspace packages import and expose metadata."""

from __future__ import annotations

import django_admin_search_query
import django_search_query


def test_search_query_version() -> None:
    """django-search-query exposes a string ``__version__``."""
    assert isinstance(django_search_query.__version__, str)
    assert django_search_query.__version__


def test_admin_search_query_version() -> None:
    """django-admin-search-query exposes a string ``__version__``."""
    assert isinstance(django_admin_search_query.__version__, str)
    assert django_admin_search_query.__version__
