"""Python <-> JavaScript highlight-lexer parity.

The colored input colors client-side (``search-lexer.js``), so the JS lexer is
a second copy of the grammar in :mod:`django_search_query.highlight`. This test
runs one adversarial corpus through both and asserts identical
``(start, role, text)`` spans, so any drift between the two engines is loud
instead of silent.

When ``node`` is on ``PATH`` the JS lexer is executed for real and compared to
Python live. Otherwise the run is marked ``SPIKE`` and falls back to a captured
golden fixture that at least pins the Python side against regression.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import typing as t

import pytest

from django_search_query.highlight import apply_registry_errors, highlight_query_spans
from django_search_query.registry import FieldRegistry, FieldSpec

# One registry, two consumers: the Python ``FieldRegistry`` and the JS
# ``applyRegistryErrors``, which reads the JSON ``SCHEMA`` derived from it (the
# shape ``search_tokens_view`` emits). Deriving both from one source is what
# makes the ``error``-role pass comparable across engines.
REGISTRY = FieldRegistry(
    specs=(
        FieldSpec(name="title", kind="string"),
        FieldSpec(name="author", kind="string", aliases=("by",)),
        FieldSpec(name="status", kind="enum", enum_values=("open", "draft", "closed")),
        FieldSpec(
            name="created",
            kind="date",
            supports_comparison=True,
            supports_range=True,
        ),
    ),
)

SCHEMA: dict[str, t.Any] = {
    "fields": [
        {
            "name": spec.name,
            "kind": spec.kind,
            "enum_values": list(spec.enum_values),
            "aliases": list(spec.aliases),
        }
        for spec in REGISTRY.specs
    ],
    "default_fields": ["title", "body"],
}

# Adversarial on purpose: uppercase keywords vs. non-keywords, unterminated
# quotes, emoji/astral chars, out-of-enum and unknown fields, negation sigils,
# comparisons/ranges, wildcards, tabs, and the Unicode edge cases where Python
# ``re`` and JS ``RegExp`` disagree unless the port is careful (accented and
# CJC letters after a keyword; U+001C/U+0085 whitespace; U+FEFF non-whitespace).
CORPUS: tuple[str, ...] = (
    "",
    "   ",
    "hello world",
    "status:open",
    "STATUS:OPEN",
    'status:open author:tony "exact phrase" NOT draft',
    "a OR b",
    "a or b",
    "ORe test",
    "OR",
    "ORé",
    "NOTx",
    "NOT x",
    "-draft +open",
    "created:>=2024-01-01",
    "created:[2024-01-01 TO 2024-12-31]",
    "created:{a TO b}",
    "(a OR b) AND c",
    "foo* *bar a?c",
    'unterminated "phrase',
    "unterminated 'phrase",
    "weird % ^ chars",
    "status:*",
    "tab\tand\nnewline",
    "🙂 status:open",
    "café status:open",
    "五 status",
    "x\x1cy",
    "a﻿b",
    "a\x85b",
    "status:bogus",
    "nope:x",
    "by:tony",
    "status: bogus",
    "\\",
)

GOLDEN_PATH = pathlib.Path(__file__).parent / "lexer_parity_golden.json"

_DRIVER = """\
const fs = require("fs");
const L = require(process.argv[2]);
const data = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const out = data.corpus.map((q) => [
  q,
  L.applyRegistryErrors(L.highlightQuerySpans(q), data.schema).map((s) => [
    s.start,
    s.role,
    s.text,
  ]),
]);
process.stdout.write(JSON.stringify(out));
"""


def _lexer_path() -> pathlib.Path:
    """Return the on-disk path to the shipped ``search-lexer.js`` asset."""
    import django_admin_search_query

    package = pathlib.Path(django_admin_search_query.__file__).parent
    return package / "static" / "django_admin_search_query" / "search-lexer.js"


def _python_spans(query: str) -> list[list[t.Any]]:
    """Lex ``query`` with the Python engine into ``[start, role, text]`` rows."""
    spans = apply_registry_errors(highlight_query_spans(query), REGISTRY)
    return [[span.start, span.role, span.text] for span in spans]


def _run_js(tmp_path: pathlib.Path) -> dict[str, list[list[t.Any]]]:
    """Execute the JS lexer over the corpus via ``node`` and return its spans."""
    driver = tmp_path / "driver.js"
    driver.write_text(_DRIVER, encoding="utf-8")
    data = tmp_path / "data.json"
    data.write_text(
        json.dumps({"schema": SCHEMA, "corpus": list(CORPUS)}),
        encoding="utf-8",
    )
    result = subprocess.run(
        ["node", str(driver), str(_lexer_path()), str(data)],
        capture_output=True,
        text=True,
        check=True,
    )
    return dict(json.loads(result.stdout))


def test_lexer_parity(tmp_path: pathlib.Path) -> None:
    """Python and JS emit byte-identical spans for every adversarial query."""
    node = shutil.which("node")
    if node is None:
        # SPIKE: no node on PATH -- the JS lexer cannot be executed here. Fall
        # back to the captured golden fixture so the Python side is still
        # regression-pinned, then skip so the run does not falsely claim parity.
        golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
        for query in CORPUS:
            assert _python_spans(query) == golden[query]
        pytest.skip("SPIKE: node not found; JS lexer not executed (golden only)")

    js_spans = _run_js(tmp_path)
    for query in CORPUS:
        assert js_spans[query] == _python_spans(query), f"lexer drift for {query!r}"
