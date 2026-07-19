"""Seed the colored-input dev harness with a superuser and sample articles."""

from __future__ import annotations

import typing as t

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from test_app.models import Article

_SAMPLE_ARTICLES: tuple[dict[str, str], ...] = (
    {
        "title": "Launch checklist",
        "status": "open",
        "author": "tony",
        "body": "ship it",
    },
    {"title": "Draft roadmap", "status": "draft", "author": "jane", "body": "planning"},
    {"title": "Closed retro", "status": "closed", "author": "tony", "body": "wrap up"},
    {"title": "Open questions", "status": "open", "author": "sam", "body": "todo list"},
)


class Command(BaseCommand):
    """Create the ``admin/admin`` superuser and a few sample articles."""

    help = "Seed a superuser (admin/admin) and sample Article rows for the dev server."

    def handle(self, *args: t.Any, **options: t.Any) -> None:
        """Idempotently create the superuser and sample rows."""
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@example.com",
                password="admin",  # local dev harness only
            )
            self.stdout.write(self.style.SUCCESS("created superuser admin/admin"))

        now = timezone.now()
        created = 0
        for sample in _SAMPLE_ARTICLES:
            _, was_created = Article.objects.get_or_create(
                title=sample["title"],
                defaults={**sample, "created": now},
            )
            created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(f"ensured {len(_SAMPLE_ARTICLES)} articles")
        )
