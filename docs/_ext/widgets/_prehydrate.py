"""Prevent flash-of-wrong-selection on the ``package-install`` widget.

The widget's server-rendered HTML always marks the first package tab and
the first method tab ``aria-selected="true"`` and hides every panel
except the ``(core, uv-add)`` cell. ``widget.js`` then reads
``localStorage`` and mutates the DOM to the user's saved selection — a
visible flash on initial page paint and on every gp-sphinx SPA
navigation between docs pages.

This module emits an inline ``<head>`` script that copies the saved
selection from ``localStorage`` onto ``<html>`` as
``data-package-install-package`` / ``data-package-install-method``
*before first paint*, plus a ``<style>`` block whose attribute-selector
rules light the active package tab, the active method tab, and show the
one matching ``(package, method)`` panel from those attributes.
``<html>`` is never replaced by gp-sphinx's ``spa-nav.js`` (it only
swaps ``.article-container``), so the attributes survive SPA navigation
and the new article paints in the saved state without the head script
re-running.

Every rule lives in ``@layer package-install-prehydrate`` and is
``!important``. The inline ``<style>`` lands in Furo's ``metatags`` slot,
before any stylesheet ``<link>``, so it is present before first paint.
Putting it in its own cascade layer keeps its ``!important`` rules
authoritative regardless of stylesheet order: per CSS Cascade Level 5
the layer ordering is *reversed* for ``!important`` declarations, so a
layered ``!important`` rule outranks an unlayered ``!important`` one of
any specificity. That reversal is load-bearing for the panel-active
rule, which must un-hide the saved panel even though it still carries
the native ``hidden`` attribute that ``widget.css``'s unlayered
``.dsq-package-install__panel[hidden]{display:none !important}`` (and the
UA/theme ``[hidden]`` default) would otherwise keep collapsed. The
reversal only applies to ``!important`` — a *normal* layered rule loses
to a *normal* unlayered one — so the tab colours are ``!important`` too,
to beat ``widget.css``'s unlayered ``.dsq-package-install__tab
[aria-selected="true"]`` look on first paint.
"""

from __future__ import annotations

import typing as t

from .package_install import DEFAULT_METHOD, DEFAULT_PACKAGE, METHODS, PACKAGES

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx


# Deactivate the server-default-selected tabs (first package + first
# method) once the html attr is present; the active selectors below then
# re-light the correct tab. Split by kind so each row keys on its own
# ``data-package-install-*`` attribute.
_TAB_DEACTIVATE_RULE = (
    "html[data-package-install-package] .dsq-package-install__tab"
    '[data-tab-kind="package"][aria-selected="true"],'
    "html[data-package-install-method] .dsq-package-install__tab"
    '[data-tab-kind="method"][aria-selected="true"]'
    "{color:var(--color-foreground-muted) !important;"
    "border-bottom-color:transparent !important;"
    "background:transparent !important}"
)

_TAB_ACTIVE_DECL = (
    "{color:var(--color-brand-primary) !important;"
    "border-bottom-color:var(--color-brand-primary) !important;"
    "background:var(--color-background-primary) !important}"
)

_PANEL_HIDE_RULE = (
    "html[data-package-install-package] "
    ".dsq-package-install__panel:not([hidden]){display:none !important}"
)

_PANEL_ACTIVE_DECL = "{display:block !important}"


def _tab_active_selectors(kind: str, ids: tuple[str, ...]) -> str:
    """Return comma-joined active-tab selectors for one axis, keyed on html."""
    return ",".join(
        f'html[data-package-install-{kind}="{id_}"] .dsq-package-install__tab'
        f'[data-tab-kind="{kind}"][data-tab-value="{id_}"]'
        for id_ in ids
    )


def _panel_active_selectors() -> str:
    """One selector per ``(package, method)`` pair.

    Both ``data-package-install-package`` and
    ``data-package-install-method`` must match for a panel to show, so
    the two axes stay independent — switching one attr never reveals a
    panel from the other axis' old value.
    """
    return ",".join(
        f'html[data-package-install-package="{p.id}"]'
        f'[data-package-install-method="{m.id}"]'
        f" .dsq-package-install__panel"
        f'[data-package="{p.id}"][data-method="{m.id}"]'
        for p in PACKAGES
        for m in METHODS
    )


def _build_style() -> str:
    """Return the ``<style>`` block driving active state from html attrs.

    Selectors are enumerated from :data:`PACKAGES` / :data:`METHODS`, so
    adding a package or method auto-extends the prehydrate rules — no
    second source of truth to drift from.
    """
    package_ids = tuple(p.id for p in PACKAGES)
    method_ids = tuple(m.id for m in METHODS)
    rules = [
        _TAB_DEACTIVATE_RULE,
        _tab_active_selectors("package", package_ids) + _TAB_ACTIVE_DECL,
        _tab_active_selectors("method", method_ids) + _TAB_ACTIVE_DECL,
        _PANEL_HIDE_RULE,
        _panel_active_selectors() + _PANEL_ACTIVE_DECL,
    ]
    return "<style>@layer package-install-prehydrate{" + "".join(rules) + "}</style>"


def _script() -> str:
    """Inline ``<head>`` script that mirrors localStorage onto ``<html>``.

    Sets both axes before first paint:
    ``data-package-install-package`` and ``data-package-install-method``,
    falling back to :data:`DEFAULT_PACKAGE` / :data:`DEFAULT_METHOD`.
    """
    return (
        '<script data-cfasync="false">(function(){'
        "try{"
        "var h=document.documentElement;"
        'var p=localStorage.getItem("dsq.package-install.package")||"'
        + DEFAULT_PACKAGE
        + '";'
        'var m=localStorage.getItem("dsq.package-install.method")||"'
        + DEFAULT_METHOD
        + '";'
        'h.setAttribute("data-package-install-package",p);'
        'h.setAttribute("data-package-install-method",m);'
        "}catch(_){}"
        "})();</script>"
    )


def _snippet() -> str:
    return _build_style() + _script()


def inject_package_install_prehydrate(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, t.Any],
    doctree: object,
) -> None:
    """Inject the package-install prehydrate ``<style>`` + ``<script>``.

    Appended to ``context["metatags"]`` so it lands in Furo's
    ``metatags`` slot (rendered before stylesheets and the ``<body>``
    open). The pair is small and a no-op when no widget is present, so we
    don't bother scoping to pages that use the directive.
    """
    context["metatags"] = context.get("metatags", "") + _snippet()
