"""Models for the query-language test suite."""

from __future__ import annotations

from django.db import models


class Article(models.Model):
    """A simple article row spanning every queryable field kind."""

    title = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=[("open", "Open"), ("draft", "Draft"), ("closed", "Closed")],
    )
    author = models.CharField(max_length=100)
    body = models.TextField()
    created = models.DateTimeField()

    def __str__(self) -> str:
        """Return the article title for admin display."""
        return self.title
