(colored-input)=

# Colored search input

The colored input is a progressive enhancement of the Django admin changelist
search box. It is **server-authoritative**: the highlighting is produced by the
Python engine and fetched over HTTP, so there is no second, drifting copy of the
grammar in JavaScript.

## How it works

`SearchQueryAdminMixin` renders the search box through a per-admin
`change_list.html` that carries two `data-*` attributes on the input, and pulls
in `search-input.js` / `search-input.css` through its `class Media`.

On load, the script replaces the plain `<input>` with a single-line `<textarea>`
layered over an `aria-hidden` overlay. The textarea's own text is transparent
(the caret stays visible); the overlay paints the colors. On every edit the
script debounces (~120 ms) and fetches the highlight endpoint, then renders the
returned spans into the overlay.

```text
keystroke -> debounce ~120ms -> GET search-highlight/?q=... -> render spans
```

Because the text is redrawn locally on every keystroke and only the *coloring*
waits for the round-trip, the visible text never lags -- only the colors do.

## Endpoints

`get_urls()` prepends two model-scoped, staff-gated JSON endpoints to the
admin's URLs (prepended so the admin's trailing `<path:object_id>` catch-all
does not swallow them).

### `search-tokens/`

Named `<app>_<model>_search_tokens`. Returns the registry schema the
autocomplete needs -- one entry per field plus the default search fields:

```json
{
  "fields": [
    {
      "name": "status",
      "kind": "enum",
      "operators": [],
      "enum_values": ["open", "draft", "closed"],
      "aliases": []
    }
  ],
  "default_fields": ["title", "body"]
}
```

The script fetches this once and caches it.

### `search-highlight/`

Named `<app>_<model>_search_highlight`. Given `?q=`, it returns the spans that
color the query:

```json
{
  "query": "status:bogus",
  "spans": [
    {"start": 0, "role": "field", "text": "status"},
    {"start": 6, "role": "punct", "text": ":"},
    {"start": 7, "role": "error", "text": "bogus"}
  ]
}
```

The spans come from `highlight_query_spans`, a whole-string lexer that covers
every character (including whitespace and unterminated quotes) and never raises.
A second pass, `apply_registry_errors`, upgrades fields and values the registry
rejects -- an unknown field, or an out-of-enum value like `status:bogus` above
-- to the `error` role. That registry awareness is the payoff of computing
colors on the server: a client-only tokenizer cannot know the schema.

## Roles

Each span carries one role; the CSS maps roles to colors (light and dark):
`whitespace`, `field`, `punct`, `keyword`, `negation`, `operator`, `wildcard`,
`phrase`, `value`, and `error`.

## Resilience

- **Stale / out-of-order responses.** Each request carries a sequence number
  and aborts the previous one with an `AbortController`; a reply is applied only
  if it is the newest *and* the textarea still holds the text it was fetched
  for.
- **Offline / network failure.** The optimistic local redraw already shows the
  correct text, so a failed fetch just means "no colors yet" -- typing is never
  blocked.
- **No JavaScript.** The original input still submits `?q=`, so the box never
  regresses below stock admin.

## Autocomplete

Typing offers a keyboard-navigable dropdown driven by the token endpoint: field
names on a bare prefix, and enum values after `field:` for enum fields.
`ArrowUp` / `ArrowDown` move the selection, `Enter` accepts it (or submits the
form when nothing is selected), and `Escape` closes it.

## Development server

`just dev` migrates a file-backed SQLite database, seeds a superuser
(`admin` / `admin`) and a few articles, and runs `runserver` with static files
and browser auto-reload so you can watch the input react to edits.
