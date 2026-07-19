"""Exceptions raised while parsing a search query string.

The parse pipeline raises exactly one error type, :class:`QueryParseError`,
so callers can degrade gracefully (e.g. the admin mixin falls back to
Django's default search on any parse failure).
"""

from __future__ import annotations


class QueryParseError(ValueError):
    """Raised when a query string cannot be tokenized or parsed.

    Carries the byte offset into the original query so callers can render a
    caret-style pointer at the offending character.

    Parameters
    ----------
    message : str
        Human-readable description of the failure.
    position : int
        Zero-based offset into the source query where the error occurred.

    Examples
    --------
    >>> err = QueryParseError("unexpected token", position=4)
    >>> err.position
    4
    >>> isinstance(err, ValueError)
    True
    """

    def __init__(self, message: str, *, position: int) -> None:
        super().__init__(message)
        self.position: int = position


__all__ = ["QueryParseError"]
