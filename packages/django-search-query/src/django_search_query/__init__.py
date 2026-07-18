"""django-search-query: a reusable search query language for Django.

The package accepts a structured, human-friendly search string and
translates it into Django-compatible query behavior, giving applications a
consistent search syntax without prescribing a particular user interface,
admin integration, or search backend.

Scope is intentionally loose. The syntax draws inspiration from Lucene --
field-scoped terms, quoted phrases, boolean operators, and grouping -- but
does not claim full Lucene compatibility or identical semantics.

This is a scaffold: the tokenizer, parser, AST, and query builder are not
implemented yet.
"""

from __future__ import annotations

import logging

from .__about__ import __version__

# Library code must never configure logging handlers, levels, or formatters
# -- that is the consuming application's job. A NullHandler keeps Python from
# emitting "No handlers could be found" warnings when the app stays silent.
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = ["__version__"]
