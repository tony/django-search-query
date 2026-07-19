(colored-input)=

# Colored search input

The colored input is a progressive enhancement of the Django admin changelist
search box. Highlighting is **client-side**: `search-lexer.js` is a faithful
JavaScript port of the Python highlighter, so the box recolors synchronously on
every keystroke with no per-edit network round-trip. A parity test keeps the two
copies of the grammar from drifting.

## How it works

`SearchQueryAdminMixin` renders the search box through a per-admin
`change_list.html` that carries a `data-*` config element, and pulls in
`search-lexer.js`, `search-input.js`, and `search-input.css` through its
`class Media` (the lexer loads first; the widget reads it as `window.DSQLexer`).

On load, the script enhances the stock `<input id=searchbar>`: it copies the
themed box metrics off `#searchbar` (font, line-height, padding, border-width,
box-sizing) onto a new native `<input class=dsq-editor>` and an `aria-hidden`
`<div class=dsq-mirror>` behind it. The editor's text is transparent (the caret
stays visible); the mirror paints the role-classed spans. Because an
`<input>`'s auto height equals a one-line `<div>`'s once those metrics match,
height and vertical alignment fall out for free -- no row math, no descender
clipping.

```text
keystroke -> DSQLexer.highlightQuerySpans + applyRegistryErrors -> render spans
```

Coloring never leaves the browser, so there is no stagger and no intermediate
un-colored frame: the mirror is rebuilt on the same tick as the keystroke.

## Python <-> JavaScript parity

`search-lexer.js` mirrors `_TOKEN_RE`, `highlight_query_spans`, and
`apply_registry_errors` alternative-for-alternative. Two Python/JS regex
differences are handled explicitly:

- **Whitespace.** Python's Unicode `\s` counts U+001C-U+001F and U+0085 as
  whitespace but not U+FEFF; JS `\s` is the reverse. The JS class is spelled out
  (`\t\n\v\f\r\x1c-\x1f\x85\p{Zs}\p{Zl}\p{Zp}`) to match Python exactly.
- **Word char.** The keyword lookahead uses Python's Unicode `\w`; JS `\w` is
  ASCII-only. The port uses `[\p{L}\p{N}_]` so `ORé` and `NOTx` stay values in
  both engines.

Offsets are re-accumulated as code points (not UTF-16 units) so `start` matches
Python for emoji and astral input.

`tests/test_lexer_parity.py` runs one adversarial corpus through both engines
and asserts identical `(start, role, text)` spans. It executes the JS lexer with
`node` when available; otherwise it marks the run `SPIKE` and falls back to a
captured golden fixture.

## Endpoints

`get_urls()` prepends two model-scoped, staff-gated JSON endpoints to the
admin's URLs (prepended so the admin's trailing `<path:object_id>` catch-all
does not swallow them).

### `search-tokens/`

Named `<app>_<model>_search_tokens`. Returns the registry schema the client
needs -- one entry per field plus the default search fields -- so the browser
can both flag `error` roles and drive autocomplete without a second schema:

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

Named `<app>_<model>_search_highlight`. Given `?q=`, it returns the same spans
the client computes. The enhanced input no longer calls it per keystroke; it is
retained as a **no-JS fallback reference** and as the canonical Python output
the parity test pins the JS port against.

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

## Roles

Each span carries one role; the CSS maps roles to colors (light and dark):
`whitespace`, `field`, `punct`, `keyword`, `negation`, `operator`, `wildcard`,
`phrase`, `value`, and `error`. Roles are color-only -- no `font-weight` change
-- so glyph advance widths stay identical between the editor and its mirror.

## Autocomplete

Typing offers a keyboard-navigable listbox driven by the token schema: field
names on a bare prefix, and enum values after `field:` for enum fields. The
combobox is hand-rolled to the @github/combobox-nav contract -- DOM focus never
leaves the input, navigation is `aria-activedescendant`, and the active option
alone carries `aria-selected`. `ArrowUp`/`ArrowDown`/`Home`/`End` move the
selection, `Enter`/`Tab` commit it, and `Escape` closes the list. A commit
splices the active token in place by offsets rather than rebuilding the string.

The suggestion source is local today, but flows through a debounced, abortable
controller keyed by `(field, fragment)`, so a server-backed field can be added
without changing the call sites.

## Resilience

- **Offline / network failure.** Coloring needs no network, so it works
  offline; only the one-time schema fetch (autocomplete + `error` roles) needs
  the server, and it degrades to plain coloring if it fails.
- **No JavaScript.** The original input still submits `?q=`, so the box never
  regresses below stock admin.

## Development server

`just dev` migrates a file-backed SQLite database, seeds a superuser
(`admin` / `admin`) and a few articles, and runs `runserver` with static files
and browser auto-reload so you can watch the input react to edits.
