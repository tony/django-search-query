/* Package install widget — SPA-safe two-axis tab sync + localStorage.
 *
 * Two independent tab rows (package x method). Uses document-level event
 * delegation so listeners survive gp-sphinx SPA navigation (which swaps
 * .article-container via .replaceWith()). Saved localStorage state is
 * re-applied on DOMContentLoaded and on every gp-sphinx:navigated event.
 *
 * Visibility is fully CSS-driven by <html data-package-install-*> attrs
 * and the @layer package-install-prehydrate rules in
 * docs/_ext/widgets/_prehydrate.py. This script never mutates the panels'
 * [hidden] attribute — it only keeps tab aria-selected and the two <html>
 * data-attrs in sync with the current selection; the CSS does the rest.
 *
 * Storage keys: dsq.package-install.package / dsq.package-install.method.
 *
 * Vanilla JS, no deps.
 */
(function () {
  "use strict";

  var STORAGE = {
    package: "dsq.package-install.package",
    method: "dsq.package-install.method",
  };
  var ATTR = {
    package: "data-package-install-package",
    method: "data-package-install-method",
  };
  var DEFAULTS = {
    package: "core",
    method: "uv-add",
  };
  var SYNC_EVENT = "dsq:package-install:sync";

  document.addEventListener("click", onClick);
  document.addEventListener("keydown", onKeydown);
  window.addEventListener(SYNC_EVENT, onBroadcast);

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applySavedState);
  } else {
    applySavedState();
  }
  document.addEventListener("gp-sphinx:navigated", applySavedState);

  function widgets() {
    return document.querySelectorAll(".dsq-package-install");
  }

  function ariaSelected(widget, kind) {
    var tab = widget.querySelector(
      '.dsq-package-install__tab[data-tab-kind="' + kind + '"][aria-selected="true"]'
    );
    return tab ? tab.getAttribute("data-tab-value") : null;
  }

  function readSaved(kind) {
    try {
      return localStorage.getItem(STORAGE[kind]);
    } catch (_e) {
      return null;
    }
  }

  function applySavedState() {
    if (!widgets().length) return;
    var savedPackage = readSaved("package");
    var savedMethod = readSaved("method");
    widgets().forEach(function (widget) {
      // Fall back to the server-rendered aria-selected default when
      // nothing is saved so every <html> attr is pushed either way.
      var pkg = savedPackage || ariaSelected(widget, "package") || DEFAULTS.package;
      var method = savedMethod || ariaSelected(widget, "method") || DEFAULTS.method;
      select(widget, "package", pkg, { persist: false, broadcast: false });
      select(widget, "method", method, { persist: false, broadcast: false });
      syncHtmlAttrs(widget);
    });
  }

  function select(widget, kind, value, opts) {
    var tabs = widget.querySelectorAll(
      '.dsq-package-install__tab[data-tab-kind="' + kind + '"]'
    );
    var hasMatch = false;
    tabs.forEach(function (tab) {
      var on = tab.getAttribute("data-tab-value") === value;
      if (on) hasMatch = true;
      tab.setAttribute("aria-selected", on ? "true" : "false");
      tab.setAttribute("tabindex", on ? "0" : "-1");
    });
    if (!hasMatch) return;

    // Push the widget's current state onto <html> so the prehydrate CSS
    // picks the right tab + panel for this axis.
    document.documentElement.setAttribute(ATTR[kind], value);

    if (opts.persist) {
      try {
        localStorage.setItem(STORAGE[kind], value);
      } catch (_e) {
        /* localStorage may be disabled; ignore. */
      }
    }
    if (opts.broadcast) {
      window.dispatchEvent(
        new CustomEvent(SYNC_EVENT, {
          detail: { origin: widget, kind: kind, value: value },
        })
      );
    }
  }

  // Mirror this widget's current tab state onto <html> for both axes so a
  // single-tab click still leaves the other attr in sync (read from the
  // widget's existing aria-selected state).
  function syncHtmlAttrs(widget) {
    var html = document.documentElement;
    var pkg = ariaSelected(widget, "package");
    var method = ariaSelected(widget, "method");
    if (pkg) html.setAttribute(ATTR.package, pkg);
    if (method) html.setAttribute(ATTR.method, method);
  }

  function onClick(event) {
    var tab = event.target.closest(".dsq-package-install__tab");
    if (!tab) return;
    var widget = tab.closest(".dsq-package-install");
    if (!widget) return;
    var kind = tab.getAttribute("data-tab-kind");
    var value = tab.getAttribute("data-tab-value");
    if (!kind || !value) return;
    select(widget, kind, value, { persist: true, broadcast: true });
  }

  function onKeydown(event) {
    var tab = event.target.closest(".dsq-package-install__tab");
    if (!tab) return;
    var widget = tab.closest(".dsq-package-install");
    if (!widget) return;
    var kind = tab.getAttribute("data-tab-kind");
    var tabs = Array.prototype.slice.call(
      widget.querySelectorAll(
        '.dsq-package-install__tab[data-tab-kind="' + kind + '"]'
      )
    );
    var current = tabs.indexOf(tab);
    var next = current;
    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
        next = (current + 1) % tabs.length;
        break;
      case "ArrowLeft":
      case "ArrowUp":
        next = (current - 1 + tabs.length) % tabs.length;
        break;
      case "Home":
        next = 0;
        break;
      case "End":
        next = tabs.length - 1;
        break;
      default:
        return;
    }
    event.preventDefault();
    tabs[next].focus();
    select(widget, kind, tabs[next].getAttribute("data-tab-value"), {
      persist: true,
      broadcast: true,
    });
  }

  function onBroadcast(event) {
    widgets().forEach(function (widget) {
      if (widget === event.detail.origin) return;
      select(widget, event.detail.kind, event.detail.value, {
        persist: false,
        broadcast: false,
      });
    });
  }
})();
