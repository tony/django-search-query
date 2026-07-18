"""django-admin-search-query: structured search for the Django admin.

An optional integration layer built on top of django-search-query. It brings
the structured query language to Django admin changelist pages while keeping
the core language usable on its own -- the coupling is intentionally loose so
the query package never depends on admin behavior or presentation concerns.

The package may also ship a self-contained search input implemented in
vanilla JavaScript, offering syntax highlighting, contextual suggestions, and
semantic autocomplete while degrading to a normal text field when JavaScript
is unavailable or disabled.

This is a scaffold: the admin mixin and the JavaScript input are not
implemented yet.
"""

from __future__ import annotations

import logging

from .__about__ import __version__

# Library code must never configure logging handlers, levels, or formatters
# -- that is the consuming application's job.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["__version__"]
