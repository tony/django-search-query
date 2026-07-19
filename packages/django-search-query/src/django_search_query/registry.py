"""Field registry describing which fields a query may reference.

The registry is the single source of truth for field validation. The parser
consults it to reject unknown fields and to reject comparison/range operators
on fields that do not support them, so typos and misuse fail at parse time
instead of silently matching nothing.
"""

from __future__ import annotations

import dataclasses
import typing as t

FieldKind = t.Literal["string", "enum", "date", "number"]
"""Kind of value a field accepts.

- ``string`` -- substring match (``icontains``) with wildcard support.
- ``enum`` -- exact match (``iexact``) against a closed value set.
- ``date`` -- ordered value; supports comparison and range operators.
- ``number`` -- ordered value; supports comparison and range operators.
"""


@dataclasses.dataclass(slots=True, frozen=True)
class FieldSpec:
    """Schema entry describing one queryable field.

    Parameters
    ----------
    name : str
        Canonical, user-facing field name (the token left of ``:``).
    kind : FieldKind
        Value kind, controlling how the compiler lowers ``field:value``.
    path : str
        ORM lookup path the field resolves to; defaults to ``name``.
    enum_values : tuple[str, ...]
        Allowed values when ``kind == "enum"`` (informational for v1).
    aliases : tuple[str, ...]
        Alternate names that resolve to this spec.
    supports_comparison : bool
        Whether ``>``, ``<``, ``>=``, ``<=`` are accepted.
    supports_range : bool
        Whether ``[a TO b]`` / ``{a TO b}`` ranges are accepted.
    """

    name: str
    kind: FieldKind
    path: str = ""
    enum_values: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    supports_comparison: bool = False
    supports_range: bool = False

    def __post_init__(self) -> None:
        """Default ``path`` to ``name`` when it was left blank."""
        if not self.path:
            # ``frozen=True`` blocks plain assignment; go through the base.
            object.__setattr__(self, "path", self.name)


@dataclasses.dataclass(slots=True, frozen=True)
class FieldRegistry:
    """Ordered collection of :class:`FieldSpec` with alias-aware lookup.

    Parameters
    ----------
    specs : tuple[FieldSpec, ...]
        The registered field specs. Duplicate names or aliases raise.

    Examples
    --------
    >>> registry = FieldRegistry(
    ...     specs=(
    ...         FieldSpec(name="status", kind="enum"),
    ...         FieldSpec(name="author", kind="string", aliases=("by",)),
    ...     ),
    ... )
    >>> registry.get("by").name
    'author'
    >>> registry.get("missing") is None
    True
    >>> registry.known_names()
    ('status', 'author')
    """

    specs: tuple[FieldSpec, ...]

    def __post_init__(self) -> None:
        """Reject duplicate canonical names or aliases at construction time."""
        seen: set[str] = set()
        for spec in self.specs:
            for name in (spec.name, *spec.aliases):
                if name in seen:
                    message = f"duplicate field registration for {name!r}"
                    raise ValueError(message)
                seen.add(name)

    def get(self, name: str) -> FieldSpec | None:
        """Return the spec for ``name`` (honoring aliases), else ``None``."""
        for spec in self.specs:
            if spec.name == name or name in spec.aliases:
                return spec
        return None

    def known_names(self) -> tuple[str, ...]:
        """Return every canonical field name, in registration order."""
        return tuple(spec.name for spec in self.specs)


__all__ = ["FieldKind", "FieldRegistry", "FieldSpec"]
