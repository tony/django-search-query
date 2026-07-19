# Documentation voice

This file covers the *voice* of prose under `docs/` — how to frame a
page so a reader meets the idea before its configuration surface. It
complements the repository-root `AGENTS.md`, which already governs
doctests, changelog conventions, and MyST roles. When the two overlap,
the root file wins; this one only answers the question it leaves open:
how should the prose sound?

## Who you are writing for

The default reader is a Django developer who wants to give their users
a real search box — field-scoped terms, quoted phrases, boolean logic —
without hand-rolling a parser. They are fluent in Django: querysets,
`Q` objects, `INSTALLED_APPS`, the admin. You cannot assume they know
anything about query-language internals — tokenizers, abstract syntax
trees, or how a search string becomes a `Q` object. That translation is
the thing the docs exist to explain.

A second, smaller reader extends the language: custom field maps,
validation hooks, new operators, the admin integration, or the optional
vanilla-JavaScript input. Serve them too, but mark their material opt-in
("for the rarer cases", "advanced") so the default reader knows they can
stop. Never make the common case pay a comprehension tax for the
advanced one.

## Voice

- **Second person, present tense, active.** "You pass the search
  string", not "The search string is parsed". Address the reader who is
  doing the thing.
- **Concept before configuration.** Open by saying what a feature *is*
  and what it does for the reader. The field-map dict, the allowed-field
  list, the settings keys — those are the last detail they need, not the
  first. A page that opens with "set these keys" has buried the idea
  under its mechanics.
- **Say when they can stop.** Lead with the default and the
  reassurance: a field map plus one call covers most sites; the query
  language is Lucene-*inspired*, so familiar syntax mostly just works;
  the admin integration and JavaScript input are optional. Let a skimmer
  leave after one paragraph.
- **Grant permission, don't demand attention.** "Reach for this
  when…", "for the rarer cases" — tell readers they're in the right
  place without implying they must read on.
- **Progressive disclosure.** Order by how many readers need it: run a
  search string against a queryset → tune the field map and allowed
  fields → the admin integration → custom operators and the JavaScript
  input. Each step is for a smaller audience than the last.
- **Lean on the pipeline.** The reader thinks string in, queryset out;
  the docs' mental model is the chain underneath: a tokenizer lexes the
  string, a parser builds an AST, and a builder compiles that AST into
  `Q` objects. Reinforce that chain when you explain where a feature
  hooks in.
- **Name the trade-off.** If the syntax is Lucene-inspired but not
  Lucene-compatible, say so plainly — do not imply parity you do not
  ship. When the JavaScript input degrades to a plain text field
  without JavaScript, state it; don't sell it.
- **Frame by concept, not by mechanism.** Don't headline a feature by
  its settings key in prose. Name the concept — "searchable fields" —
  and keep the key in the code block or the API reference.

## Examples that run

Sphinx doctest examples run through `just -f docs/justfile doctest`, and
autodoc examples receive the imports configured in `docs/conf.py`.
Pytest does not collect Markdown pages by itself; fenced examples that
cannot be doctested belong in focused tests under `tests/`. When a docs
page uses a `>>>` example, spell out any imports that are not in the
Sphinx doctest global setup.

Many examples in these docs never execute: fenced `console` install
blocks, settings dicts, and rendered-SQL output are prose to pytest.
They are still claims about real behavior — check them against a passing
test under `tests/` before you change them.

```{note}
The tokenizer, parser, builder, field registry, and admin mixin ship,
and the docs' `>>>` examples run as doctests. If you document behavior
that is not yet implemented, still mark it as such rather than implying
it runs today.
```

## What stays precise

Warm the framing, never the facts. Query-syntax examples
(`status:open "exact phrase"`), field-map dicts, generated `Q` objects
and SQL, and class or function cross-references carry meaning in their
exact form — leave them alone. The friendly voice belongs in the
sentences *around* a precise block, introducing it, not inside it
paraphrasing it into vagueness.

## Cross-references

Point the advanced reader at the deep-dive rather than inlining it, and
put the link where their interest peaks — on the phrase that made them
curious ("custom operators", "searchable fields") — not as a standalone
footnote the eye skips. Use the MyST roles listed in the root
`AGENTS.md` (`{class}`, `{meth}`, `{func}`, `{exc}`, `{attr}`, `{ref}`,
`{doc}`). A `{ref}` must match its target's anchor exactly. `just
build-docs` catches a broken cross-reference; the doctests do not — so
build the docs before you commit.

Link the first prose mention of any symbol that has a useful
destination on that page: Python objects, this project's APIs, Django
concepts (`Q`, querysets, the admin), topic pages, and external tools.
Use the most specific target available: `{class}`, `{meth}`, `{func}`,
`{mod}`, `{exc}`, or `{attr}` for API objects; `{ref}` or `{doc}` for
documentation pages and section anchors; a Markdown link for external
projects. After the first linked mention on a page, later mentions can
stay plain unless the distance or context makes another link useful.

## Before you commit

- Does the page open with what the feature *is*, or with how to
  configure it?
- Can a reader who needs only the defaults stop after the first
  paragraph?
- Is anything headlined by a settings key that should be named by
  concept instead?
- Are the admin and JavaScript-input parts clearly marked opt-in?
- Did you leave every settings block, query example, output block,
  table, and cross-reference exact — and do any `>>>` examples pass
  `just -f docs/justfile doctest`?
- Did `just build-docs` stay clean — no new warning, no broken
  cross-reference?
