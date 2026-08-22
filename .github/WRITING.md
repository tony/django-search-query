# Writing

How this project writes prose, for humans and agents alike. It governs
`README.md`, `CHANGES`, `MIGRATION`, commit messages, error messages,
docstrings, and source comments — every surface a reader reaches.

For environment setup, the gates, and pull request workflow, see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Voice

Three surfaces, one voice. A docstring says what a caller may rely on; a
`CHANGES` entry says what changed; prose says what happens. All three are
present tense, lead with the thing being described, and stop. Why it was built
that way belongs in the commit message, which is timestamped and attached to
the diff.

The most useful editing operation is deleting the introductory sentence.

Lead with verbs and name concrete things. Put identifiers in backticks. Prefer
short declarative sentences, one operational fact each. Do not explain Python
or Django to a Django developer; do explain this project's semantics.

Type annotations describe shape. Documentation describes meaning. A sentence
that restates a signature has said nothing.

Use MUST, SHOULD, and MAY only where the normative sense is meant. Say what
actually happens rather than that something is "supported".

| Instead of                       | Prefer                             |
| --------------------------------- | ----------------------------------- |
| "We added…"                       | "`search_query_to_q` now accepts…" |
| "New and improved"                | "`FieldRegistry` now…"             |
| "powerful", "seamless"            | state the capability               |
| "easily", "simply", "just"        | omit                                |
| "simple", "obvious", "intuitive"  | omit                                |
| "robust"                          | name the failure that is handled   |
| "comprehensive"                   | name what is covered               |
| "production-ready"                | state the guarantee                |
| "optimized", "blazingly fast"     | give the magnitude                 |
| "various fixes"                   | name the components                |
| "under the hood"                  | omit unless observable             |
| "please note that", "note that"   | state the fact                     |
| "leverage", "utilize"             | "use"                               |
| "delve into"                      | "read", or omit                    |
| "best practices"                  | name the practice                  |
| "in order to"                     | "to"                                |

## Who you are writing for

The default reader is a Django developer who wants to give their users a real
search box — field-scoped terms, quoted phrases, boolean logic — without
hand-rolling a parser. They are fluent in Django: querysets, `Q` objects,
`INSTALLED_APPS`, the admin. You cannot assume they know anything about
query-language internals — tokenizers, abstract syntax trees, or how a search
string becomes a `Q` object. That translation is what the docs exist to
explain.

A second, smaller reader extends the language: custom field maps, validation
hooks, new operators, the admin integration, or the optional vanilla-JavaScript
input. Serve them too, but mark their material opt-in ("for the rarer cases",
"advanced") so the default reader knows they can stop. Never make the common
case pay a comprehension tax for the advanced one.

Rules that follow:

- **Second person, present tense, active.** "You pass the search string", not
  "The search string is parsed". Address the reader who is doing the thing.
- **Concept before configuration.** Open by saying what a feature *is* and
  what it does for the reader. The field-map dict, the allowed-field list, the
  settings keys — those are the last detail they need, not the first. A page
  that opens with "set these keys" has buried the idea under its mechanics.
- **Say when they can stop.** Lead with the default and the reassurance: a
  field map plus one call covers most sites; the query language is
  Lucene-*inspired*, so familiar syntax mostly just works; the admin
  integration and JavaScript input are optional. Let a skimmer leave after one
  paragraph.
- **Grant permission, do not demand attention.** "Reach for this when…", "for
  the rarer cases" — tell readers they are in the right place without
  implying they must read on.
- **Progressive disclosure.** Order by how many readers need it: run a search
  string against a queryset, then tune the field map and allowed fields, then
  the admin integration, then custom operators and the JavaScript input. Each
  step is for a smaller audience than the last.
- **Lean on the pipeline.** The reader thinks string in, queryset out; the
  mental model underneath is the chain a tokenizer lexes into a parser's AST,
  which a builder compiles into `Q` objects. Reinforce that chain when
  explaining where a feature hooks in.
- **Name the trade-off.** The syntax is Lucene-inspired, not
  Lucene-compatible — say so plainly, do not imply parity that is not
  shipped. When the JavaScript input degrades to a plain text field without
  JavaScript, state it; do not sell it.
- **Frame by concept, not by mechanism.** Do not headline a feature by its
  settings key in prose. Name the concept — "searchable fields" — and keep
  the key in the code block or the API reference.

## README

A README is the shortest path from "what is this?" to competent use, not the
project's autobiography.

The first sentence is a contract. It says what abstraction the reader has been
handed, concretely enough to tell the two packages in this workspace apart.

Get to a runnable snippet before anything the reader can skip. State the
minimum Python version and Django versions in prose, not only in a table —
`requires-python` in each package's `pyproject.toml` is the authority, and the
README must agree with it. Name the distribution and the import separately
for each package (`django-search-query` installs `django_search_query`;
`django-admin-search-query` installs `django_admin_search_query`).

Document the semantic model, not a flag list — there is no CLI here, so this
means: what a query string compiles to, what an unparseable query does
(degrades to a fallback rather than raising, in the admin integration), and
what the JavaScript input does with and without JavaScript enabled.

State defaults explicitly — defaults are API. State negative guarantees where
they exist: "no UI, admin, or backend assumptions", "no per-keystroke
request", "degrades to a plain text field without JavaScript". They establish
boundaries faster than any amount of description.

Headings stay conventional and stable, because people deep-link them.

## Documented examples that run

Examples in this repository are tests. This section is the contract for
writing one the test suite can actually see, and it states this repository's
real mechanism — read it before assuming a rule from another project applies
here unchanged.

**A fence tag is cosmetic. Only a `>>> ` prompt executes.** A block written as

    ```python
    tokenize("status:open")
    ```

is prose that looks like a test. Nothing collects it, nothing runs it, and it
can be wrong for years. The same block written with a prompt is a test:

    ```python
    >>> tokenize("status:open")
    ```

Removing the prompts leaves a green test suite and a silently deleted test.
When editing a file that contains examples, count the prompts before and
after.

**The fence tag is `python`.** Not `pycon`, not bare.

**Two collectors, one convention.** `pyproject.toml` sets
`addopts = "--doctest-modules"` and lists
`packages/django-search-query/src`, `packages/django-admin-search-query/src`,
`tests`, and `docs` in `testpaths`.

- Under the two packages' `src/`, pytest's own doctest-modules collector runs
  every `>>> ` block in a docstring.
- Under `docs/`, `.md` files are collected by `pytest-doctest-docutils`
  (shipped by `gp-libs`, registered under the `sphinx` pytest plugin entry
  point) — this is why a docs page's `>>> ` blocks are real tests, not
  illustrations, and why the collection count is proof of this section.

**`README.md` is not in `testpaths`.** A `>>> ` block placed there would not
be collected or run. Do not add one; an example that looks tested but is not
is worse than one that is plainly illustrative. Show README usage examples as
plain, accurate, unprompted `python` fences instead, as
[`docs/tutorial.md`](../docs/tutorial.md) already does for its second,
non-doctested example — and say, in prose, where the same call actually is
checked (a docs `{doctest}` block, or a pinned case in
`tests/test_query_examples.py`).

**No name is available in a doctest without an explicit import.** No
`conftest.py` in this repository defines a `doctest_namespace` fixture, so
every block — under `src/` or `docs/` — must import everything it uses.
`docs/conf.py` sets `doctest_global_setup` with a handful of convenience
imports, but that only feeds Sphinx's own doctest builder
(`just -f docs/justfile doctest`, run separately from `pytest`); the pytest
collectors above do not read it. Write every docs example to work without it.

**The MyST `{doctest}` directive is already in use**, not just available —
see `docs/tutorial.md` and `docs/query.md`. Reach for it over a bare fenced
block when the surrounding prose needs the block to read as a distinct,
labeled example.

**`# doctest: +SKIP` is not permitted.** It is a workaround that tests
nothing.

**Do not downgrade a doctest to a non-executed block to make it pass.** A
`.. code-block::` or an unprompted fence does not run. If an example cannot
pass, fix the example or fix the code.

**Option flags.** `ELLIPSIS` and `NORMALIZE_WHITESPACE` are enabled globally
(`doctest_optionflags` in `pyproject.toml`), so `...` elides variable output
and whitespace differences do not fail a comparison. Reach for an inline
`# doctest: +FLAG` only for the block that needs it.

**Docstring examples** use the NumPy `Examples` section:

    Examples
    --------
    >>> from django_search_query.tokenizer import tokenize
    >>> tokenize('"a b"')[0].is_phrase
    True

**Illustrative, non-executed blocks are real content, not filler.** Fenced
`console` install blocks, settings dicts, and rendered-SQL tables in `docs/`
are prose to pytest — they never run — but they are still claims about real
behavior. Check one against a passing test under `tests/` before changing it
(`tests/test_query_showcase.py` backs the query-syntax table in
`docs/query.md`; `tests/test_query_examples.py` pins the `repr(Q)` values
quoted across the docs).

**Query syntax in prose.** Use the `` {dsq}`status:open` `` inline role (and
the ` ```dsq ` fence for a block) for query-string examples in `docs/` —
both are registered in `docs/conf.py` and syntax-highlight the same way the
admin's colored search input does. Plain backticks are for everything else:
Python identifiers, file paths, settings keys.

## The changelog

`CHANGES` is the changelog, covering both packages in one place; `MIGRATION`
is the companion deprecation and upgrade-notes file, in the same format.
Neither is `CHANGELOG.md`; both are rendered on the docs site (`docs/history.md`
includes `CHANGES` directly).

A ledger, not a narrative. It is scanned, and the question a reader is asking
is whether an entry affects them. Modeled on Django's release-notes shape:
deliverables get titles and prose, not bullets.

**Release entry boilerplate.** Every release header is
`## django-search-query X.Y.Z (YYYY-MM-DD)` — headed by the core package even
when the release only touches the admin package, which names itself in its
own `####` heading instead. `CHANGES` and `MIGRATION` each open with a single
`## django-search-query X.Y.Z (unreleased)` placeholder block, fenced by
`<!-- KEEP THIS PLACEHOLDER ... -->` and `<!-- END PLACEHOLDER ... -->` HTML
comments. New entries land immediately below the END marker, never above it.

**A release entry's lead paragraph is release-time material.** Open a
released entry with two to four sentences of plain prose, no italic, the
version as the sentence subject ("django-search-query X.Y.Z ships …") so it
reads standalone when excerpted — this doubles as the release notes; there is
no separate release-notes page. Numbers over adjectives: name the concrete
capability, not "much faster" or "many fixes". Cross-reference detail docs
with `{ref}` to keep it compact.

**The unreleased placeholder carries no lead paragraph and no version
summary** — sections only (`### Breaking changes`, `### What's new`
deliverables, `### Fixes`, …). Speaking for a release — what the version
"is", "ships", or "focuses on" — is presumptuous before its scope is final;
only the person cutting the release writes that, and only when asked to
release. Never write or edit a lead paragraph from a feature branch, and
never ask or imply that a release should happen. The same rule applies to
`MIGRATION`.

**Each deliverable is a section, not a bullet.** Inside `### What's new`,
every distinct deliverable gets a `#### Deliverable title (#NN)` heading
naming it in user vocabulary, followed by one to three prose paragraphs. Do
not wrap a paragraph in `- ` — bullets are for enumerable lists, not
paragraph containers. The deliverable test: if you cannot name the
deliverable in one sentence of user vocabulary, the entry is not ready.
Mechanism — helper internals, schema-validation locations — belongs in pull
request descriptions and code comments, not the changelog.

**Fixed subheadings**, in this order when present: `### Breaking changes`,
`### Dependencies`, `### What's new`, `### Fixes`, `### Documentation`,
`### Development`. Dev tooling (helper scripts, CI changes) lives under
`### Development`. A breaking change shows the migration path with concrete
`# Before` / `# After` code, inline in the entry — a pointer to `MIGRATION`
is not enough on its own. Dependency floor bumps use
``Minimum `pkg>=X.Y.Z` (was `>=X.Y.W`)``.

**`(#NN)`** sits in each deliverable's `####` heading.

**Bullets are for catch-alls.** `### Fixes`, and occasionally
`### Documentation`, with three or more genuinely small items use bullets —
one line each, never paragraphs. A bullet that swells past two lines gets
promoted to its own `#### Title (#NN)` heading with a prose body.

**Anti-patterns.** Fragile metrics that go stale silently — token ceilings,
third-party version pins, percent benchmarks, exact byte counts — describe
the capability, not the math. Private symbols (leading-underscore
identifiers) and internal jargon. Walls of text dressed up as bullets.
Breaking changes buried mid-entry instead of given their own subheading at
the top.

**Always link autodoc'd APIs.** Any class, method, function, exception, or
attribute with its own rendered page is cited with the matching role —
`{class}`, `{meth}`, `{func}`, `{exc}`, `{attr}` — never plain backticks. A
doc page without an explicit ref label uses `{doc}`; an anchor inside one
uses `{ref}`. Plain backticks are correct for code syntax, settings keys,
and file paths that have no autodoc destination.

**Summarization style.** Asked "what changed in the latest version?", lead
with the entry's lead paragraph (paraphrased if needed), then each `####`
deliverable heading under `### What's new` with a one-sentence summary. Cite
`(#NN)` only if asked for source links. Never invent a version, date, or
number not present in `CHANGES`; never quote a line number or file offset —
those shift as the file evolves.

## Docstrings

The prime directive: never restate the type. The annotation is the source of
truth; the docstring carries what the annotation cannot.

This is documentation debt wearing a docstring:

    def parse(query: str) -> Node:
        """Parse a query.

        Parameters
        ----------
        query : str
            The query.

        Returns
        -------
        Node
            The parsed node.
        """

Document instead the dimensions the type system cannot encode: what an
exception means and what triggers it, whether calling twice does anything the
second time, what an empty or half-typed input does, and platform or
dependency-version differences.

The first sentence stands alone; tooling truncates there. PEP 257 applies:
triple double quotes, an imperative one-line summary ending in a period, a
blank line before any extended description. Do not repeat an introspectable
signature. Style is NumPy (`ruff`'s `pydocstyle` convention is `numpy`),
enforced by the linter rather than relitigated in review.

Public functions and methods carry a working doctest once one exists for
them — see [Documented examples that run](#documented-examples-that-run) for
the mechanics: no `# doctest: +SKIP`, no downgrading to a non-executed block.
If a working doctest cannot be written for a change, say so rather than
leaving a fake one.

## Source comments

A comment ships only if it passes all three gates. Fail any: delete or
rewrite. Borderline: delete — borderline means the information is
reconstructible, which is what makes deletion cheap.

**Loss.** Three years from now, would losing this cost a maintainer real time
rediscovering intent, an invariant, a constraint, or a failure mode the code
and tests do not already make obvious?

**Elite.** Would SQLite, Redis, the Go standard library, or CPython write
this comment, at this length? Those projects state the constraint and stop.
They do not argue with an imagined objector.

**Upkeep.** Will it stay true without maintenance? A comment that hand-syncs
a value the code owns — a count, an offset, a line reference, a duplicated
constant — is false the first time that value moves.

### Ceiling

One or two lines. A comment reaching four is either carrying several facts,
in which case split it, or arguing, in which case cut it to the fact.

Rationale, alternatives weighed, and the story of how the code got here
belong in the commit message: timestamped, attached to the exact diff, and
free to maintain.

A comment often holds both a constraint and the deliberation that found it.
Keep the constraint, cut the deliberation. "Runs at most once per second"
survives; "this is the right trade for now" does not.

### Keep

- Why over how: upstream quirks, protocol and compatibility constraints,
  performance tradeoffs still part of the contract.
- Invariants, preconditions, ordering, lifetime, and concurrency requirements
  that types and tests cannot express.
- Code that looks wrong but is not, so a later cleanup does not reintroduce
  the bug.
- A high-level sketch of an algorithm whose local operations do not reveal
  the whole.

### Delete

- Narration of the next lines; code translated into English.
- Restated names, types, defaults, or control flow.
- Values duplicated from the code and hand-synced.
- Justification, hedging, or apology for a choice.
- Speculation about future requirements.
- History version control already holds, including commented-out code.
- Ticket and issue numbers. They say nothing to a reader without tracker
  access, and they rot when the tracker moves. Unfinished work goes in the
  tracker, not the source.
- Transient observations — "currently", "for now", "the latest release" —
  that go stale with no nearby edit.

### The upkeep gate in practice

It reaches values that track our own code. It does not reach frozen external
facts.

Bad (Delete):

    # There are 12 fields in the registry.

Good (Keep):

    # Keywords are case-sensitive (uppercase only), matching Lucene: a
    # lowercase "and" is a search term, not an operator.

### Documentation exception

Doctests, minimal usage examples, and parameter, return, and raises entries
on public API are exempt from the loss gate — they serve the caller, not the
maintainer. They are exempt from nothing else. Ceiling: a good man page
entry. NumPy-style `Parameters`, `Returns`, and `Attributes` sections fall
under the same exception — autodoc ships every field whether or not it is
described, and a doctest that runs is also a test.

## Terminology and capitalization

Pick the domain noun and keep it. A query is a *query string* until it is
parsed into an *AST* and compiled to a *`Q`*; do not call the AST a "parse
tree" in one paragraph and an "AST" in the next. If the function is
`search_query_to_q`, write "compile" for what it does everywhere, rather than
alternating with "translate", "convert", and "build".

Stable vocabulary is what makes search, deep links, and an agent's retrieval
work at all.

Python, Django, and PyPI keep their own capitalization. Distribution names
are written as they are published: `django-search-query`,
`django-admin-search-query`.

Do not write counts into prose — how many fields a registry supports, how
many tests there are. They go stale silently and no reader needs them.

## Markdown

Prose wraps at 80 columns. Table rows, badge lines, and long links are
exempt, because breaking them harms rendering. A pull request or issue body
does not wrap at all: GitHub renders a single newline as a space in a file
and as a line break in a comment, so a wrapped comment body arrives as ragged
stubs.

GitHub alert blocks — `> [!NOTE]`, `> [!WARNING]` — render as literal text
outside GitHub, so reserve them for at most one load-bearing warning per
document. Write the sentence so it carries the fact on its own, and a
renderer that drops the marker loses nothing.

Do not use a local absolute path or an email address in anything published.

## Code blocks

Code blocks are paste-and-run units: pasting one block runs exactly one
intended action. Executed examples are exempt — the test suite runs them,
nobody pastes them.

- **One command per block.** Multiple steps may share a block only when
  explicitly chained with `&&`, `;`, or `\` continuations — the chain is then
  one logical command.
- **Explanations go in prose above the block**, never as `#` comments inside
  it.
- **Command menus are per-command blocks with prose lead-ins**, not tables.
- **Shell commands use the `console` tag with a `$ ` prefix.** This separates
  interactive commands from scripts and enables prompt-aware copy.
- **Split long commands with `\`** — one flag or flag+value pair per
  indented continuation line, positional arguments last.

Good — show the last ten commits as a graph:

```console
$ git log \
    --max-count=10 \
    --graph \
    --oneline
```

Bad:

```console
# Show the last ten commits as a graph
$ git log --max-count=10 --graph --oneline
```

## Commits

```
Scope(type[detail]): concise description

why: Explanation of necessity or impact.

what:
- Specific technical changes made
- Focused on a single topic
```

Keep the subject to 50 characters or fewer, excluding any trailing `(#NN)`
pull request reference, and wrap body lines at 72. Separate the `why:` and
`what:` blocks with a blank line.

Routine maintenance commits drop the colon and take a capitalized
description, which is what distinguishes them at a glance in
`git log --oneline`:

```
py(deps[dev]) Bump dev packages
ai(rules[AGENTS]) Judge comments by three gates
```

Everything that changes behavior keeps the colon.

Common types:

- **feat**: New features or enhancements
- **fix**: Bug fixes
- **refactor**: Code restructuring without functional change
- **docs**: Documentation updates
- **chore**: Maintenance (dependencies, tooling, config)
- **test**: Test-related updates
- **style**: Code style and formatting
- **ci**: Workflow and pipeline changes
- **py(deps)**: Dependencies
- **py(deps[dev])**: Dev dependencies
- **ai(rules[AGENTS])**: `AGENTS.md`/`WRITING.md`/`CONTRIBUTING.md` updates
- **ai(claude[rules])**: Claude Code rules (`CLAUDE.md` beyond the symlink)
- **ai(claude[command])**: Claude Code command changes

Example:

```
Highlight(feat[range]): Flag an unterminated bracket range

why: A half-typed `created:[2024-01-01` should read as pending, not error.

what:
- Track open-bracket state while lexing a range
- Emit a `pending` role instead of `error` until the range closes
```

For a multi-line message, use a heredoc so the formatting survives:

```console
$ git commit -m "$(cat <<'EOF'
Scope(feat[detail]): Concise description

why: Explanation of the change.

what:
- First change
- Second change
EOF
)"
```

### Release commits

Never create tags. Never push tags. The owner handles tagging and tag
pushes, because a tag triggers the publish workflow — and, in this
workspace, each package is tagged and released independently of the other.

A release commit subject is plain and short: `Tag <package> v<version>` (for
example, `Tag django-search-query v0.1.0a2`). The detailed why and what go in
the body. Do not use the `Scope(type[detail]):` format for a release — it
buries the lede.

## Slop prevention

Treat AI slop as review-hostile noise, not as proof that text or code is
wrong. The goal is to maximize information density.

- **AI signatures.** No "Generated by", no conversational filler, no
  unexplained emoji, no tool metadata.
- **Brittle references.** No hard-coded line numbers, fragile file or test
  counts, dated "as of" claims, bare SHAs, or local absolute paths — unless
  they are strict evidentiary artifacts such as a benchmark log or a pinned
  fixture value.
- **Durable source links.** Link to a pinned revision, never to `master`. A
  `blob/master/…` link rots silently as the file moves or lines shift while
  still resolving. Prefer a release tag (`blob/v0.1.0a1/…`); otherwise a
  7-character commit SHA reachable from `master`, never a pull-request-head
  SHA that can be rebased away. Reserve `blob/master/…` for a living document
  meant to always show the latest state, such as this repository's own
  `CONTRIBUTING.md`. A line anchor (`#L120-L145`) is only safe on a pinned
  ref.
- **Diff narration.** Do not restate what moved, was renamed, or was removed
  in anything the reader holds alongside the diff: code, docstrings,
  `README.md`, `CHANGES`, or a pull request description. The diff and the
  commit message already carry it.
- **Branch-internal narrative.** Do not mention intermediate states,
  abandoned approaches, or "no longer" behavior unless users of the most
  recently published release actually experienced the old state — deprecation
  notes and `### Fixes` entries for bugs a published release shipped are the
  exception; they stay.
- **Low-value scaffolding.** No ownerless TODOs, unused future-proofing,
  debug artifacts, or defensive wrappers around failure modes nothing can
  reach.
- **Prose inflation.** The diction table under [Voice](#voice) governs;
  replace an inflated word with a concrete description of behavior,
  constraints, or trade-offs.
- **Coded labels.** Write rules and findings as plain imperatives. No `[R1]`,
  `Option B`, or any index a reader has to decode.

Preserve the "why". Never delete a comment documenting an invariant, a
protocol constraint, a platform quirk, or an upstream workaround — those are
the facts [Source comments](#source-comments) keeps, and every other comment
is judged by it. Exact counts, dates, and SHAs that serve as evidence in
benchmark results, release notes, or lockfiles are immune from the brittle-
reference rule above.
