(dsq-explanation)=

# Explanation

## The pipeline

A search string becomes a {class}`~django.db.models.Q` through three stages,
each owned by one module. The tokenizer classifies characters into a token
stream and records their source offsets, deferring every grammar decision to
the parser. The parser is a precedence-climbing (Pratt) parser: it consumes
the token stream and builds an AST, validating each field it meets against a
{class}`~django_search_query.registry.FieldRegistry` as it goes, so an
unknown field or an unsupported operator raises
{exc}`~django_search_query.errors.QueryParseError` before compilation ever
starts. {func}`~django_search_query.build_q` lowers that AST into a Django
`Q` with a single structural `match` -- adding a new ORM mapping never
touches parsing, and adding new syntax never touches the ORM mapping.

```dsq
status:open OR status:draft
```

```text
"status:open OR status:draft"
    -> tokenize()   characters -> Token stream (ident, colon, term, or, ...)
    -> parse()      Pratt parser -> AST: Term | Field | Cmp | Range | Exists
                                          | Not | And | Or
    -> build_q()    structural match -> Django Q
```

{func}`~django_search_query.parse` and `build_q` are the two halves of that
middle-and-last stage; {func}`~django_search_query.search_query_to_q`
chains tokenizing, parsing, and building for the common case in one call.
`AND` and `OR` are left-associative, `OR` binds loosest, and `NOT`/`-`/`+`
bind tightest as prefixes, so `NOT a AND b` parses as `(NOT a) AND b` --
juxtaposition (`a b`) is an implicit `AND` sharing its binding power, so
`a b` and `a AND b` parse identically.

## Why two lexers exist

The tokenizer above is strict on purpose: it raises
{exc}`~django_search_query.errors.QueryParseError` on the first malformed
character, which is exactly what a query compiler should do -- fail loud
rather than silently compile the wrong query. A live search box needs the
opposite guarantee: it has to colorize every keystroke, including a query
that is only half-typed -- an unterminated quote, a dangling `[`.

For that, the package ships a second, presentation-only lexer,
`highlight_query_spans`, that never raises. It runs one regex over the
entire string, with a catch-all group absorbing any character it cannot
classify, so the span list it returns always covers the source end to end.
The two lexers share no code: keeping them independent means a change meant
to loosen highlighting can never accidentally loosen what the parser
accepts, and vice versa. It is also why `?` can color as a wildcard in the
search box while the compiler still treats it as a literal character -- see
{doc}`../../query` for that boundary case, and
{doc}`../django-admin-search-query/colored-input` for the JavaScript port of
this same lexer that colors the admin search box client-side.

## Lucene-inspired, not Lucene-compatible

The syntax borrows familiar [Lucene] shapes -- field-scoped terms
({dsq}`status:open`), quoted phrases, `AND`/`OR`/`NOT`, grouping, comparisons,
and ranges -- but the package does not claim full Lucene compatibility, and
some gaps are permanent rather than pending. There is no fuzzy match
(`~`), no boosting (`^`), and no proximity search. `?` is not a
single-character wildcard, even though Lucene defines it as one: the
compiler only ever implements `*`. Treat the syntax as a small, predictable
subset of Lucene's rather than a drop-in replacement for it.

[Lucene]: https://lucene.apache.org/
