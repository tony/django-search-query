"""Package install + quickstart picker widget: package x method matrix.

Renders two independent tab rows — one choosing which distribution to
install, one choosing how — and, for every ``(package, method)`` pair, a
panel pairing the install command with that package's Python quickstart.

The two axes are orthogonal:

- **PACKAGE** picks the distribution: ``core``
  (``django-search-query``, the query language) or ``admin``
  (``django-admin-search-query``, the optional admin integration). The
  quickstart shown alongside the command differs per package — the core
  :func:`~django_search_query.search_query_to_q` call or the admin
  ``SearchQueryAdminMixin`` setup.
- **METHOD** picks the tool: ``uv-add`` (``uv add``) or ``pip``
  (``pip install``).

Every combination is a server-rendered panel; switching either axis is
driven entirely by ``<html>`` data-attributes (see ``_prehydrate.py``),
so one axis never depends on the other's client state.
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass

from ._base import BaseWidget

if t.TYPE_CHECKING:
    import collections.abc as cabc

    from sphinx.environment import BuildEnvironment


@dataclass(frozen=True, slots=True)
class Package:
    """One installable distribution row in the picker.

    ``dist`` is the PyPI distribution name that fills each method's
    install command. ``quickstart`` is the Python snippet shown after
    that command — it renders through the ``python`` Pygments lexer.
    """

    id: str
    label: str
    dist: str
    quickstart: str


@dataclass(frozen=True, slots=True)
class Method:
    """One install method (``uv add`` / ``pip install``).

    ``template`` is the install command with a ``{dist}`` placeholder
    filled per package in :func:`build_panels`.
    """

    id: str
    label: str
    template: str


@dataclass(frozen=True, slots=True)
class Panel:
    """Pre-built HTML-ready cell for one ``(package, method)`` pair.

    ``code_a_body`` is the install command (rendered ``console``);
    ``code_b_body`` is the package quickstart (rendered ``python``).
    """

    package: Package
    method: Method
    code_a_body: str
    code_b_body: str
    is_default: bool


_CORE_QUICKSTART = """\
from django_search_query import search_query_to_q
from django_search_query.registry import FieldRegistry, FieldSpec

registry = FieldRegistry(specs=(FieldSpec(name="status", kind="enum"),))
q = search_query_to_q(
    "status:open",
    registry=registry,
    field_map={"status": "status"},
    default_fields=("title", "body"),
)
Article.objects.filter(q)
"""


# Built by implicit concatenation, not a triple-quoted block: the
# ``search_query_registry`` line renders at 89 columns, one past the 88
# ruff enforces on this source file. Splitting it here keeps the
# displayed snippet byte-for-byte intact while every source line stays
# under the limit.
_ADMIN_QUICKSTART = (
    "from django.contrib import admin\n"
    "\n"
    "from django_admin_search_query import SearchQueryAdminMixin\n"
    "from django_search_query.registry import FieldRegistry, FieldSpec\n"
    "\n"
    "\n"
    "@admin.register(Article)\n"
    "class ArticleAdmin(SearchQueryAdminMixin, admin.ModelAdmin):\n"
    "    search_query_registry = FieldRegistry("
    'specs=(FieldSpec(name="status", kind="enum"),))\n'
    '    search_query_field_map = {"status": "status"}\n'
    '    search_query_default_fields = ("title", "body")\n'
)


PACKAGES: tuple[Package, ...] = (
    Package(
        id="core",
        label="django-search-query",
        dist="django-search-query",
        quickstart=_CORE_QUICKSTART,
    ),
    Package(
        id="admin",
        label="django-admin-search-query",
        dist="django-admin-search-query",
        quickstart=_ADMIN_QUICKSTART,
    ),
)


METHODS: tuple[Method, ...] = (
    Method(id="uv-add", label="uv add", template="uv add {dist}"),
    Method(id="pip", label="pip install", template="pip install {dist}"),
)


DEFAULT_PACKAGE: str = PACKAGES[0].id
DEFAULT_METHOD: str = METHODS[0].id


def build_panels(
    packages: tuple[Package, ...] = PACKAGES,
    methods: tuple[Method, ...] = METHODS,
) -> list[Panel]:
    """Pre-build one panel per ``(package, method)``.

    The first pair (``core``, ``uv-add``) is marked default so its
    panel is the one server-rendered without ``hidden`` — the no-JS
    fallback and the pre-hydration base state.
    """
    panels: list[Panel] = []
    for package_index, package in enumerate(packages):
        for method_index, method in enumerate(methods):
            command = method.template.format(dist=package.dist)
            panels.append(
                Panel(
                    package=package,
                    method=method,
                    code_a_body=f"$ {command}",
                    code_b_body=package.quickstart,
                    is_default=(package_index == 0 and method_index == 0),
                )
            )
    return panels


class PackageInstallWidget(BaseWidget):
    """The ``{package-install}`` Sphinx directive."""

    name = "package-install"
    option_spec: t.ClassVar[cabc.Mapping[str, t.Callable[[str], t.Any]]] = {}
    default_options: t.ClassVar[cabc.Mapping[str, t.Any]] = {}

    @classmethod
    def context(cls, env: BuildEnvironment) -> cabc.Mapping[str, t.Any]:
        """Provide packages, methods, panels + defaults to the Jinja template."""
        return {
            "packages": PACKAGES,
            "methods": METHODS,
            "panels": build_panels(),
            "default_package": DEFAULT_PACKAGE,
            "default_method": DEFAULT_METHOD,
        }
