"""Django settings for the django-search-query workspace test suite.

Installs both workspace apps plus the admin and its supporting apps so the
admin integration package can be exercised from a single ``pytest`` run.
"""

from __future__ import annotations

import typing as t

SECRET_KEY = "not very secret in tests"

DATABASES: dict[str, t.Any] = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}

USE_TZ = True

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django_search_query",
    "django_admin_search_query",
    "test_app",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = "tests.urls"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
