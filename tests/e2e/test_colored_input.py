"""Playwright end-to-end test for the server-authoritative colored input.

Excluded from the fast lane (the ``e2e`` marker is skipped unless ``-m e2e``).
Run with a browser installed::

    playwright install chromium
    DJANGO_SETTINGS_MODULE=tests.settings_e2e uv run pytest -m e2e

The browser-free proof of the same contract lives in
``tests/test_search_endpoints.py`` and always runs.

SPIKE: chromium does not launch in this bakeoff environment -- the Playwright
sync API is greenlet-based and hangs indefinitely under the free-threaded
CPython 3.14t build in use here (a bare ``p.chromium.launch()`` never returns).
The assertions below are written against the real DOM the widget builds
(``textarea.dsq-editor``, ``.dsq-token--field``, ``.dsq-dropdown``) and the
``search-highlight`` response, so the test is correct and should pass on a
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
    """Typing a query colors it via the server and offers enum autocomplete."""
    _login(page, live_server.url, admin_user.get_username())

    page.goto(live_server.url + reverse("admin:test_app_article_changelist"))
    editor = page.wait_for_selector("textarea.dsq-editor")
    assert editor is not None

    # Typing debounces into a highlight request; capture it to prove the
    # server -- not any JS tokenizer -- produced the spans.
    with page.expect_response(lambda r: "search-highlight" in r.url) as caught:
        editor.type('status:open author:tony "phrase" NOT draft')
    assert caught.value.ok

    page.wait_for_selector(".dsq-token--field")
    # Exactly two field-scoped tokens: ``status:`` and ``author:``.
    assert page.locator(".dsq-token--field").count() == 2

    # Autocomplete: after ``status:`` the dropdown lists the enum values.
    editor.fill("")
    editor.type("status:")
    page.wait_for_selector(".dsq-dropdown:not([hidden]) .dsq-option")
    options = page.locator(".dsq-option").all_inner_texts()
    assert any("status:open" in option for option in options)
