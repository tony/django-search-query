"""Pytest configuration scoped to the ``docs`` tree.

``--doctest-modules`` (set in the root ``pyproject.toml``) walks every
``.py`` file under ``testpaths``, which includes ``docs``. The widget
framework under ``docs/_ext`` is Sphinx build-time infrastructure, not
library code documented by example -- it carries no ``>>>`` doctests, so
excluding it here keeps the doctest lane from failing on modules that were
never meant to have one.
"""

from __future__ import annotations

collect_ignore = ["_ext"]
