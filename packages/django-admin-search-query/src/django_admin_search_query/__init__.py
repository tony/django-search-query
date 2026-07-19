"""django-admin-search-query: structured search for the Django admin.

An optional integration layer built on top of django-search-query. It brings
the structured query language to Django admin changelist pages while keeping
the core language usable on its own -- the coupling is intentionally loose so
the query package never depends on admin behavior or presentation concerns.

:class:`~django_admin_search_query.mixin.SearchQueryAdminMixin` brings the
structured query language to changelist search boxes, degrading to Django's
built-in ``search_fields`` behavior for plain or unparseable terms.
"""

from __future__ import annotations

import logging

from .__about__ import __version__
from .mixin import SearchQueryAdminMixin

# Library code must never configure logging handlers, levels, or formatters
# -- that is the consuming application's job.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["SearchQueryAdminMixin", "__version__"]
