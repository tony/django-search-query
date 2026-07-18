(releasing)=

# Releasing

Each package is versioned and released **independently**. A release touches
one package's version and changelog without requiring changes to the other.

The version literal lives in two places per package:

- `packages/<name>/pyproject.toml` -- `[project].version`
- `packages/<name>/src/<module>/__about__.py` -- `__version__`

Publishing is driven by CI on tag push. Tags are created and pushed by a
maintainer, never by tooling.

```{note}
Because the admin integration depends on the core package through a loose
floor (`django-search-query>=X`), the two can be released on separate
cadences.
```
