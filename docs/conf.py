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

import django
from gp_sphinx.config import make_workspace_linkcode_resolve, merge_sphinx_config

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

# Names available to every `>>>` block in the docs (sphinx.ext.doctest).
# Django is already configured above via django.setup().
doctest_global_setup = """
from django.db.models import Q
from django_search_query import build_q, parse, search_query_to_q
from django_search_query.registry import FieldRegistry, FieldSpec
"""

# Keep django_search_query imported so linkcode can resolve its source.
_ = django_search_query


def setup(app: object) -> dict[str, bool]:
    """Register the ``dsq`` query-language lexer for MyST code fences."""
    from django_search_query.pygments_lexer import DjangoSearchQueryLexer

    app.add_lexer("dsq", DjangoSearchQueryLexer)  # ty: ignore[unresolved-attribute]
    return {"parallel_read_safe": True, "parallel_write_safe": True}
