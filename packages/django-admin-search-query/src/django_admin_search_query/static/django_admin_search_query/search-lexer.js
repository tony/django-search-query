/*
 * django-admin-search-query: client-side query highlighter.
 *
 * A faithful JavaScript port of Python's
 * `django_search_query.highlight.highlight_query_spans` +
 * `apply_registry_errors`. Coloring runs entirely in the browser, so the
 * overlay repaints synchronously on every keystroke with no network hop.
 *
 * The `tests/test_lexer_parity.py` corpus runs the SAME adversarial strings
 * through this file (via node) and the Python lexer and asserts identical
 * (start, role, text) spans, so any drift between the two is caught in CI
 * rather than shipping as a silent mismatch.
 *
 * UMD wrapper: `module.exports` under node (the parity harness), a
 * `window.DSQLexer` global in the browser (loaded before search-input.js).
 */
(function (root, factory) {
  "use strict";
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.DSQLexer = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Drift mitigation 1 -- whitespace.
  // Python's `re` `\s` (Unicode) and JS `\s` disagree at the edges: Python
  // treats U+001C-U+001F and U+0085 as whitespace and U+FEFF as NOT; JS `\s`
  // is the reverse. Spell the class out to match Python exactly:
  // ASCII controls + `\p{Zs}` (space separators) + `\p{Zl}`/`\p{Zp}` (line/
  // paragraph separators). This deliberately excludes U+FEFF, which Python
  // keeps inside a value token.
  var WS = "\\t\\n\\v\\f\\r\\x1c-\\x1f\\x85\\p{Zs}\\p{Zl}\\p{Zp}";

  // Drift mitigation 2 -- word char.
  // The keyword lookahead uses Python's Unicode `\w`; JS `\w` is ASCII-only.
  // `[\p{L}\p{N}_]` reproduces `str.isalnum()`-plus-underscore so `ORe`,
  // `NOTx`, and `ORé` stay values (a keyword must be UPPERCASE and terminated
  // by a non-word char) in both engines.
  var WORD = "\\p{L}\\p{N}_";

  // Same alternatives, same order, same semantics as Python's `_TOKEN_RE`.
  // Order matters: the most specific branch that can start at a position wins,
  // and `misc` (`.`) is a single-char catch-all so every character is covered.
  var PATTERN =
    "(?<whitespace>[" + WS + "]+)" +
    "|(?<phrase>\"(?:\\\\.|[^\"\\\\])*\"?|'(?:\\\\.|[^'\\\\])*'?)" +
    "|(?<field>[A-Za-z_][A-Za-z0-9_]*)(?=:)" +
    "|(?<keyword>(?:AND|OR|NOT|TO)(?![" + WORD + "]))" +
    "|(?<operator>>=|<=|[<>])" +
    "|(?<punct>[:()\\[\\]{}])" +
    "|(?<negation>(?<![^" + WS + "([{])[-+])" +
    "|(?<wildcard>[*?])" +
    "|(?<value>[^" + WS + ":()\\[\\]{}<>*?\"'+]+)" +
    "|(?<misc>.)";

  // `u` for `\p{}` + code-point matching of astral chars (emoji); `g` for
  // matchAll. Deliberately no `s` flag: like Python's non-DOTALL `.`, `misc`
  // must not swallow newlines (whitespace already owns them).
  var TOKEN_RE = new RegExp(PATTERN, "gu");

  // `misc` (an unclassifiable single char) reads as a value so a stray symbol
  // colors like the term it sits in rather than vanishing -- mirrors Python.
  var MISC_ROLE = "value";

  var HIGHLIGHT_ROLES = [
    "whitespace",
    "field",
    "punct",
    "keyword",
    "negation",
    "operator",
    "wildcard",
    "phrase",
    "value",
    "error",
  ];

  function codePointLength(text) {
    // Python offsets are code-point indices; JS string indices are UTF-16.
    // Spread counts code points (astral chars as one), keeping `start` aligned
    // with Python for emoji/astral input.
    return Array.from(text).length;
  }

  // Lex `query` into contiguous {start, role, text} spans covering it end to
  // end. Never throws: an unterminated quote or lone bracket still yields a
  // full span list, exactly like the Python lexer.
  function highlightQuerySpans(query) {
    var spans = [];
    var offset = 0;
    var matches = query.matchAll(TOKEN_RE);
    for (var match of matches) {
      var text = match[0];
      var groups = match.groups;
      var role = MISC_ROLE;
      for (var name in groups) {
        if (groups[name] !== undefined) {
          role = name === "misc" ? MISC_ROLE : name;
          break;
        }
      }
      spans.push({ start: offset, role: role, text: text });
      offset += codePointLength(text);
    }
    return spans;
  }

  function getSpec(schema, name) {
    var fields = (schema && schema.fields) || [];
    for (var i = 0; i < fields.length; i++) {
      var field = fields[i];
      if (field.name === name) {
        return field;
      }
      var aliases = field.aliases || [];
      if (aliases.indexOf(name) >= 0) {
        return field;
      }
    }
    return null;
  }

  // Mirror of Python's `_value_index_after_field`: a predicate lexes as
  // field `:` value, optionally with one whitespace span after the colon.
  // Returns the value span index, or -1 for comparisons/ranges (no enum).
  function valueIndexAfterField(spans, fieldIndex) {
    var colonIndex = fieldIndex + 1;
    if (colonIndex >= spans.length) {
      return -1;
    }
    var colon = spans[colonIndex];
    if (colon.role !== "punct" || colon.text !== ":") {
      return -1;
    }
    var valueIndex = colonIndex + 1;
    if (valueIndex < spans.length && spans[valueIndex].role === "whitespace") {
      valueIndex += 1;
    }
    if (
      valueIndex < spans.length &&
      (spans[valueIndex].role === "value" || spans[valueIndex].role === "phrase")
    ) {
      return valueIndex;
    }
    return -1;
  }

  // Registry-aware second pass, mirroring Python's `apply_registry_errors`:
  // an unknown field re-roles both the field and its value to `error`; an
  // out-of-enum value re-roles only the value. Returns a new array.
  function applyRegistryErrors(spans, schema) {
    var result = spans.map(function (span) {
      return { start: span.start, role: span.role, text: span.text };
    });
    for (var i = 0; i < result.length; i++) {
      var span = result[i];
      if (span.role !== "field") {
        continue;
      }
      var spec = getSpec(schema, span.text);
      var valueIndex = valueIndexAfterField(result, i);
      if (spec === null) {
        result[i].role = "error";
        if (valueIndex >= 0) {
          result[valueIndex].role = "error";
        }
        continue;
      }
      if (
        spec.kind === "enum" &&
        spec.enum_values &&
        spec.enum_values.length &&
        valueIndex >= 0
      ) {
        var value = result[valueIndex];
        if (value.role === "value" && spec.enum_values.indexOf(value.text) < 0) {
          result[valueIndex].role = "error";
        }
      }
    }
    return result;
  }

  return {
    HIGHLIGHT_ROLES: HIGHLIGHT_ROLES,
    highlightQuerySpans: highlightQuerySpans,
    applyRegistryErrors: applyRegistryErrors,
  };
});
