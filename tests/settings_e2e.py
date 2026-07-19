"""End-to-end settings: test settings plus static-file serving for Playwright.

Used only by ``DJANGO_SETTINGS_MODULE=tests.settings_e2e uv run pytest -m e2e``
so ``live_server`` serves the colored-input JS and CSS to a real browser.
"""

from __future__ import annotations

import os

from tests.settings import *  # noqa: F403

# Playwright's sync API runs the test under a greenlet event loop, which trips
# Django's async-unsafe guard when pytest-django sets up the database. The DB
# work is genuinely synchronous, so the guard is a false positive here.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

STATIC_URL = "/static/"

INSTALLED_APPS = [
    *INSTALLED_APPS,  # noqa: F405
    "django.contrib.staticfiles",
]
