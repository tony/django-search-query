"""Sphinx configuration for the django-search-query workspace docs.

A single documentation site covers every workspace package. Each package's
``src`` directory is put on ``sys.path`` so autodoc can import it directly
during development, and ``gp_sphinx.config.merge_sphinx_config`` wires up the
shared git-pull design system (theme, fonts, MyST, copybutton, tabs, SEO).
"""

from __future__ import annotations

import os
import pathlib
import sys
import typing as t

import django
from gp_sphinx.config import make_workspace_linkcode_resolve, merge_sphinx_config

if t.TYPE_CHECKING:
    from docutils import nodes
    from sphinx.application import Sphinx

# Project layout
cwd = pathlib.Path(__file__).parent
project_root = cwd.parent
packages_root = project_root / "packages"

# Allow importing tests.settings and every workspace package during the build.
sys.path.insert(0, str(project_root))
for _pkg in sorted(packages_root.glob("*/src")):
    sys.path.insert(0, str(_pkg))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
django.setup()

import django_search_query  # noqa: E402

# Umbrella metadata comes from the core package.
about_path = (
    packages_root
    / "django-search-query"
    / "src"
    / "django_search_query"
    / "__about__.py"
)
about: dict[str, str] = {}
with about_path.open() as fp:
    exec(fp.read(), about)

conf = merge_sphinx_config(
    project=about["__title__"],
    version=about["__version__"],
    copyright=about["__copyright__"],
    source_repository=f"{about['__github__']}/",
    docs_url=about["__docs__"],
    source_branch="master",
    light_logo="img/icons/logo.svg",
    dark_logo="img/icons/logo-dark.svg",
    html_favicon="_static/favicon.ico",
    html_extra_path=["manifest.json"],
    extra_extensions=[
        "sphinx.ext.doctest",
        "sphinx_autodoc_api_style",
        "docs._ext.widgets",
    ],
    intersphinx_mapping={
        "python": ("https://docs.python.org/3/", None),
        "django": (
            "https://docs.djangoproject.com/en/stable/",
            "https://docs.djangoproject.com/en/stable/_objects/",
        ),
    },
    linkcode_resolve=make_workspace_linkcode_resolve(
        repo_root=project_root,
        github_url=about["__github__"],
        source_branch="master",
    ),
    set_type_checking_flag=True,
    rediraffe_redirects="redirects.txt",
    # AGENTS.md / CLAUDE.md are agent guidance, not site pages; keep Sphinx
    # from treating them as orphan documents.
    exclude_patterns=["_build", "AGENTS.md", "CLAUDE.md"],
)
globals().update(conf)

# Class-var annotations render as ``t.ClassVar[...]`` (the ``import typing as
# t`` alias), which nitpicky autodoc cannot resolve to a real target. It is a
# typing construct, not a documentable class, so silence it rather than chase
# an anchor that does not exist.
nitpick_ignore = [("py:class", "t.ClassVar")]

# Names available to every `>>>` block in the docs (sphinx.ext.doctest).
# Django is already configured above via django.setup().
doctest_global_setup = """
from django.db.models import Q
from django_search_query import build_q, parse, search_query_to_q
from django_search_query.highlight import apply_registry_errors, highlight_query_spans
from django_search_query.registry import FieldRegistry, FieldSpec
"""

# Keep django_search_query imported so linkcode can resolve its source.
_ = django_search_query


def _dsq_inline_role(
    name: str,
    rawtext: str,
    text: str,
    lineno: int,
    inliner: object,
    options: dict[str, t.Any] | None = None,
    content: list[str] | None = None,
) -> tuple[list[nodes.Node], list[nodes.system_message]]:
    """Inline ``{dsq}`status:open` `` role: highlight query syntax inline.

    Reuses the same ``DjangoSearchQueryLexer`` the ```` ```dsq ```` fences use,
    emitting an inline ``<code class="highlight">`` whose token spans pick up
    the theme's class-scoped Pygments colors in both light and dark mode.
    """
    from docutils import nodes, utils
    from pygments import highlight
    from pygments.formatters.html import HtmlFormatter

    from django_search_query.pygments_lexer import DjangoSearchQueryLexer

    inner = highlight(
        utils.unescape(text), DjangoSearchQueryLexer(), HtmlFormatter(nowrap=True)
    ).strip()
    html = f'<code class="highlight dsq-inline">{inner}</code>'
    return [nodes.raw("", html, format="html")], []


def setup(app: Sphinx) -> dict[str, bool]:
    """Register the ``dsq`` fence lexer, the ``{dsq}`` inline role, and its CSS."""
    from django_search_query.pygments_lexer import DjangoSearchQueryLexer

    app.add_lexer("dsq", DjangoSearchQueryLexer)
    app.add_role("dsq", _dsq_inline_role)
    app.add_css_file("css/dsq-inline.css")
    return {"parallel_read_safe": True, "parallel_write_safe": True}
