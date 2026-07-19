"""Dev-server settings for the colored-input harness (``just dev``).

Layers static-file serving and browser auto-reload on top of the test settings
so ``manage.py runserver`` renders the enhanced admin search box with live JS
and CSS. Not used by the test suite.
"""

from __future__ import annotations

import pathlib

from tests.settings import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
STATIC_URL = "/static/"
# Annotated so ty accepts the override of the star-imported literal.
ROOT_URLCONF: str = "tests.urls_dev"

# A file-backed database (not the tests' in-memory one) so ``migrate``,
# ``seed_dev``, and ``runserver`` -- separate processes -- share the same rows.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(pathlib.Path(__file__).resolve().parent.parent / "dev.sqlite3"),
    },
}

INSTALLED_APPS = [
    *INSTALLED_APPS,  # noqa: F405
    "django.contrib.staticfiles",
    "django_browser_reload",
]

MIDDLEWARE = [
    *MIDDLEWARE,  # noqa: F405
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]
