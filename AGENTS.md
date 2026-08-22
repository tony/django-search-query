# AGENTS.md

`django-search-query` is a [uv] workspace shipping two independently
versioned Django packages: a Lucene-inspired search query language, and an
optional admin integration built on top of it.

Follow the conventions already in the tree, and keep a change scoped to what
was asked for.

## What is here

| Path                             | What it is                                                  |
| --------------------------------- | ------------------------------------------------------------ |
| `pyproject.toml`                  | Workspace root: members, shared ruff/ty/pytest/coverage config; no `[project]` of its own |
| `packages/django-search-query/`   | Core query language (`django_search_query`): tokenizer, parser, AST, compiler, field registry, highlighter |
| `packages/django-admin-search-query/` | Optional admin integration (`django_admin_search_query`): the search mixin and the vanilla-JS colored input |
| `packages/AGENTS.md`              | Logging conventions for the two packages' library code      |
| `tests/`                          | Shared pytest suite for both packages (Django settings, fixtures, e2e) |
| `test_app/`                       | Django test app and `seed_dev` command backing the dev server and e2e tests |
| `docs/`                           | Single Sphinx site (gp-sphinx) documenting both packages     |
| `CHANGES` / `MIGRATION`           | Workspace-wide changelog and migration notes (root, not per-package) |
| `justfile`                        | Task runner: test/lint/format/type-check/docs recipes        |

## Which policy applies

- Documentation, user-facing text, `CHANGES`, release notes, commit messages,
  docstrings, and source comments:
  [.github/WRITING.md](.github/WRITING.md)
- Environment, the gates, tests, documentation builds, releases, and pull
  requests: [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md)

Each of those is the single home for its subject. Where a rule seems to be
stated twice, the file listed above is the one that governs.

## Change discipline

- Make the smallest coherent change that solves the verified problem; keep
  unrelated cleanup out of it.
- Reuse an existing file, helper, API, or test before adding a new one.
- Add a file only for a durable boundary — a distinct responsibility,
  independent reuse, or splitting an oversized module — not for a single-use
  helper or a one-line re-export.
- Add a test for every user-visible behaviour change, and a `CHANGES` entry
  for every change to the public API, admin integration, or JavaScript input.
- A passing gate is evidence only once it has been shown capable of failing.
  Pair a new test with a deliberate break that proves it bites.

The highlighting grammar is duplicated on purpose: `highlight.py` (Python, in
the core package) and `search-lexer.js` (its JavaScript port, in the admin
package's static assets) must stay lexeme-for-lexeme in sync —
`tests/test_lexer_parity.py` checks this against Node when it is on `PATH`,
and against a captured fixture otherwise. Both packages are versioned and
released independently (`0.1.0aN`); a change to one does not bump the other.

## References

- Documentation: <https://django-search-query.git-pull.com>
- Changelog: `CHANGES` (root); migration notes: `MIGRATION` (root)
- PyPI: <https://pypi.org/project/django-search-query/> and
  <https://pypi.org/project/django-admin-search-query/>
- uv workspaces: <https://docs.astral.sh/uv/concepts/projects/workspaces/>

[uv]: https://docs.astral.sh/uv/
