"""Playwright end-to-end test for the client-highlighted colored input.

Excluded from the fast lane (the ``e2e`` marker is skipped unless ``-m e2e``).
Run with a browser installed::

    playwright install chromium
    DJANGO_SETTINGS_MODULE=tests.settings_e2e uv run pytest -m e2e

The browser-free proof of the same contract lives in
``tests/test_search_endpoints.py`` and always runs; the Python<->JS lexer
parity that underwrites the client-side coloring lives in
``tests/test_lexer_parity.py``.

SPIKE: chromium does not launch in this bakeoff environment -- the Playwright
sync API is greenlet-based and hangs indefinitely under the free-threaded
CPython 3.14t build in use here (a bare ``p.chromium.launch()`` never returns).
The assertions below are written against the real DOM the widget builds (native
``input.dsq-editor``, the ``.dsq-mirror`` overlay, ``.dsq-token--field`` spans,
and the ``.dsq-listbox`` combobox), so the test is correct and should pass on a
standard CPython build with the browser installed; it simply cannot be executed
here.
"""

from __future__ import annotations

import typing as t

import pytest
from django.urls import reverse

if t.TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from playwright.sync_api import Page
    from pytest_django.live_server_helper import LiveServer

pytestmark = pytest.mark.e2e


def _login(page: Page, base_url: str, username: str) -> None:
    """Sign in through the admin login form as ``username`` (password ``password``)."""
    page.goto(base_url + reverse("admin:login"))
    page.fill("#id_username", username)
    page.fill("#id_password", "password")
    page.click("input[type=submit]")


@pytest.mark.django_db
def test_colored_input_highlights_and_autocompletes(
    page: Page,
    live_server: LiveServer,
    admin_user: AbstractUser,
) -> None:
    """Typing a query colors it client-side and offers enum autocomplete."""
    _login(page, live_server.url, admin_user.get_username())

    page.goto(live_server.url + reverse("admin:test_app_article_changelist"))
    editor = page.wait_for_selector("input.dsq-editor")
    assert editor is not None

    # No network round-trip: coloring is produced by search-lexer.js, so the
    # field-scoped tokens appear in the mirror as soon as the value changes.
    editor.fill('status:open author:tony "phrase" NOT draft')
    page.wait_for_selector(".dsq-mirror .dsq-token--field")
    # Exactly two field-scoped tokens: ``status:`` and ``author:``.
    assert page.locator(".dsq-mirror .dsq-token--field").count() == 2

    # An out-of-enum value is flagged ``error`` entirely on the client, using
    # the schema fetched once from ``search-tokens/``.
    editor.fill("status:bogus")
    page.wait_for_selector(".dsq-mirror .dsq-token--error")
    assert page.locator(".dsq-mirror .dsq-token--error").inner_text() == "bogus"

    # Autocomplete: after ``status:`` the listbox lists the enum values, with
    # DOM focus never leaving the input (aria-activedescendant navigation).
    editor.fill("status:")
    page.wait_for_selector(".dsq-listbox:not([hidden]) .dsq-option")
    options = page.locator(".dsq-option").all_inner_texts()
    assert any("status:open" in option for option in options)
    assert editor.get_attribute("role") == "combobox"
    assert editor.get_attribute("aria-expanded") == "true"
