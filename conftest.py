"""Root pytest configuration for the django-search-query workspace."""

from __future__ import annotations

import typing as t

import pytest

if t.TYPE_CHECKING:
    import collections.abc as cabc

# Dev/e2e-only settings and URL configs are imported by their own Django
# process, never as doctest modules; ignoring them keeps ``--doctest-modules``
# from importing dev-only dependencies during the fast lane.
collect_ignore = [
    "manage.py",
    "tests/settings_dev.py",
    "tests/settings_e2e.py",
    "tests/urls_dev.py",
]


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: cabc.Iterable[pytest.Item],
) -> None:
    """Skip ``e2e`` tests unless the run explicitly selects them with ``-m e2e``.

    The browser end-to-end suite is slow and needs a Playwright browser, so it
    stays out of the default lane. Running ``pytest -m e2e`` opts back in.
    """
    markexpr = config.getoption("markexpr", default="")
    if isinstance(markexpr, str) and "e2e" in markexpr:
        return
    skip_e2e = pytest.mark.skip(reason="e2e: select with -m e2e")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)
