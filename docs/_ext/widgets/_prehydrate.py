"""Prevent flash-of-wrong-selection on the ``library-install`` widget.

The widget's server-rendered HTML always marks the first method tab
``aria-selected="true"`` and shows only the first method's panel.
``widget.js`` then reads ``localStorage`` and mutates the DOM to the
user's saved selection — a visible flash on initial page paint and on
every gp-sphinx SPA navigation between docs pages.

This module emits an inline ``<head>`` script that copies the saved
selection from ``localStorage`` onto ``<html>`` as
``data-library-install-method`` *before first paint*. The CSS rules
that drive panel visibility from that attribute live in
``docs/_widgets/library-install/widget.css`` — both stylesheet and
widget JS read the same storage key.
"""

from __future__ import annotations

import typing as t

from .library_install import DEFAULT_METHOD

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx


def _library_install_snippet() -> str:
    """Return the inline ``<script>`` that replays the saved install method."""
    return (
        '<script data-cfasync="false">(function(){'
        "try{"
        'var m=localStorage.getItem("dsq.library-install.method.v2")'
        '||"' + DEFAULT_METHOD + '";'
        'document.documentElement.setAttribute("data-library-install-method",m);'
        "}catch(_){}"
        "})();</script>"
    )


def inject_library_install_prehydrate(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, t.Any],
    doctree: object,
) -> None:
    """Inject the library-install prehydrate snippet into Furo's ``<head>``."""
    context["metatags"] = context.get("metatags", "") + _library_install_snippet()
