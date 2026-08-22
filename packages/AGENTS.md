# AGENTS.md

Logging conventions for library code in `django-search-query` and
`django-admin-search-query` (`*/src/`). Everything else — environment, gates,
prose policy, commit format — is set at the repository root; see
[../AGENTS.md](../AGENTS.md).

## Logger setup

- Use `logging.getLogger(__name__)` in every module.
- Add a `NullHandler` in each package's `__init__.py`.
- Never configure handlers, levels, or formatters in library code — that is
  the consuming application's job.

## Structured context via `extra`

Pass structured data on a log call where it is useful for filtering,
searching, or test assertions. `snake_case`, `django_` prefix, stable scalars
— avoid ad-hoc objects.

Keys already emitted and treated as compatibility-sensitive — a downstream
user may build a dashboard or alert on one, so change a meaning deliberately:

| Key                        | Type  | Emitted by                          |
| --------------------------- | ----- | ------------------------------------ |
| `django_search_query_len`   | `int` | tokenizer, parser, admin mixin       |
| `django_search_field`       | `str` | parser, on an unknown field          |

## Lazy formatting

`logger.debug("msg %s", val)`, not an f-string. Deferred interpolation is
skipped entirely when the level is filtered, and a log aggregator groups
`"%s"`-style templates into one signature instead of one per unique message.
Guard an expensive `val` with `if logger.isEnabledFor(logging.DEBUG)`.

## `stacklevel` for wrappers

Increment it for each wrapper layer so `%(filename)s:%(lineno)d` points at
the real caller. Verify whenever call depth changes.

## Log levels

| Level     | Use for                             | Examples                          |
| --------- | ------------------------------------ | ---------------------------------- |
| `DEBUG`   | Internal mechanics                   | Tokenizer/parser start, positions  |
| `INFO`    | Lifecycle, user-visible operations   | Query compiled                     |
| `WARNING` | Recoverable issues, deprecation      | Unknown search field ignored       |
| `ERROR`   | Failures that stop an operation      | Parse error                        |

## Message style

Lowercase, past tense for events ("parse started", "unknown field"). No
trailing punctuation. Details go in `extra`, not the message string.

## Exception logging

Use `logger.exception()` only inside an `except` block you are not
re-raising from. Use `logger.error(..., exc_info=True)` for a traceback
outside an `except` block. Avoid `logger.exception()` followed by `raise` —
it duplicates the traceback; add context via `extra` instead, or let the
exception propagate.

## Testing logs

Assert on `caplog.records` attributes, not string matching on `caplog.text`:

- Scope capture:
  `caplog.at_level(logging.DEBUG, logger="django_search_query.parser")`.
- Filter by record, not position:
  `[r for r in caplog.records if hasattr(r, "django_search_field")]`.
- `caplog.record_tuples` cannot see `extra` fields — use `caplog.records`.

## Avoid

- f-strings or `.format()` in a log call.
- Unguarded logging in a hot loop (guard with `isEnabledFor()`).
- Catch-log-reraise without adding new context.
- `print()` for diagnostics.
- Logging a secret env var's value (log the key name only).
- A non-scalar, ad-hoc object in `extra`.
- A custom `extra` field referenced in the format string without a safe
  default — a missing key raises `KeyError`.
