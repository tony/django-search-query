/*
 * django-admin-search-query: server-authoritative colored search input.
 *
 * Strategy: there is NO JavaScript tokenizer. The admin search box is enhanced
 * into a textarea layered over an aria-hidden overlay. On every edit we debounce
 * (~120ms) and fetch the highlight endpoint, which returns (start, role, text)
 * spans produced by the Python `highlight_query_spans` plus a registry-aware
 * `error` role. The overlay renders exactly those spans, so the coloring can
 * never drift from the engine. The textarea's text is transparent (caret still
 * visible); the overlay shows the colors. With JS off, the original <input>
 * still submits ?q= untouched.
 */
(function () {
  "use strict";

  var DEBOUNCE_MS = 120;

  /* ---- token-endpoint schema cache (one fetch per URL, shared) ---------- */
  var schemaCache = Object.create(null);

  function loadSchema(url) {
    if (!schemaCache[url]) {
      schemaCache[url] = fetch(url, { credentials: "same-origin" })
        .then(function (r) {
          return r.ok ? r.json() : { fields: [], default_fields: [] };
        })
        .catch(function () {
          return { fields: [], default_fields: [] };
        });
    }
    return schemaCache[url];
  }

  /* ---- overlay rendering ------------------------------------------------- */

  // Render server spans into the overlay. Each span becomes a role-classed
  // <span>; whitespace is preserved by `white-space: pre` on the overlay.
  function renderSpans(overlay, spans) {
    overlay.textContent = "";
    for (var i = 0; i < spans.length; i++) {
      var span = spans[i];
      var el = document.createElement("span");
      el.className = "dsq-token dsq-token--" + span.role;
      el.textContent = span.text;
      overlay.appendChild(el);
    }
    // A trailing zero-width box keeps the overlay tall when the value is empty
    // and lets a trailing space stay measurable for scroll sync.
    overlay.appendChild(document.createTextNode("​"));
  }

  // Instant, un-colored render so the visible text never lags the keystroke;
  // only the coloring waits for the server round-trip.
  function renderPlain(overlay, value) {
    overlay.textContent = value + "​";
  }

  /* ---- caret-context parsing for autocomplete (NOT query parsing) ------- */

  // Slice out the whitespace-delimited token the caret sits in. This is a
  // presentation aid for the dropdown only; it never interprets the query.
  function caretToken(value, caret) {
    var start = caret;
    while (start > 0 && !/\s/.test(value[start - 1])) {
      start--;
    }
    return { start: start, text: value.slice(start, caret) };
  }

  // Given a caret token, decide what to suggest: enum values after `field:`
  // for an enum field, otherwise matching field names.
  function suggestionsFor(token, schema) {
    var colon = token.text.indexOf(":");
    if (colon >= 0) {
      var name = token.text.slice(0, colon).replace(/^[-+]/, "");
      var prefix = token.text.slice(colon + 1);
      var field = fieldByNameOrAlias(schema, name);
      if (field && field.enum_values && field.enum_values.length) {
        return field.enum_values
          .filter(function (v) {
            return v.indexOf(prefix) === 0;
          })
          .map(function (v) {
            return { label: name + ":" + v, insert: name + ":" + v, kind: "value" };
          });
      }
      return [];
    }
    var bare = token.text.replace(/^[-+]/, "");
    return (schema.fields || [])
      .filter(function (f) {
        return f.name.indexOf(bare) === 0;
      })
      .map(function (f) {
        return { label: f.name + ":", insert: f.name + ":", kind: f.kind };
      });
  }

  function fieldByNameOrAlias(schema, name) {
    var fields = schema.fields || [];
    for (var i = 0; i < fields.length; i++) {
      if (fields[i].name === name) {
        return fields[i];
      }
      var aliases = fields[i].aliases || [];
      if (aliases.indexOf(name) >= 0) {
        return fields[i];
      }
    }
    return null;
  }

  /* ---- the widget -------------------------------------------------------- */

  function enhance(input) {
    var highlightUrl = input.dataset.highlightUrl;
    var tokensUrl = input.dataset.searchTokensUrl;
    if (!highlightUrl) {
      return;
    }

    var form = input.form;
    var wrap = document.createElement("div");
    wrap.className = "dsq-wrap";

    var overlay = document.createElement("div");
    overlay.className = "dsq-overlay";
    overlay.setAttribute("aria-hidden", "true");

    var editor = document.createElement("textarea");
    editor.className = "dsq-editor";
    editor.name = input.name || "q";
    editor.value = input.value;
    editor.rows = 1;
    editor.setAttribute("wrap", "off");
    editor.setAttribute("autocomplete", "off");
    editor.setAttribute("autocapitalize", "off");
    editor.setAttribute("autocorrect", "off");
    editor.setAttribute("spellcheck", "false");
    editor.setAttribute("role", "combobox");
    editor.setAttribute("aria-autocomplete", "list");
    editor.setAttribute("aria-expanded", "false");
    // Preserve the admin label/help association by inheriting the id.
    if (input.id) {
      editor.id = input.id;
    }
    if (input.getAttribute("aria-describedby")) {
      editor.setAttribute("aria-describedby", input.getAttribute("aria-describedby"));
    }

    var dropdown = document.createElement("ul");
    dropdown.className = "dsq-dropdown";
    dropdown.setAttribute("role", "listbox");
    dropdown.hidden = true;

    wrap.appendChild(overlay);
    wrap.appendChild(editor);
    wrap.appendChild(dropdown);
    // Replacing the <input> drops its name="q", so only the textarea submits.
    input.replaceWith(wrap);

    var state = {
      seq: 0, // monotonically-increasing request id; stale replies are ignored
      controller: null, // AbortController for the in-flight highlight request
      schema: { fields: [], default_fields: [] },
      items: [], // current dropdown suggestions
      active: -1, // highlighted dropdown index
    };

    if (tokensUrl) {
      loadSchema(tokensUrl).then(function (schema) {
        state.schema = schema;
      });
    }

    /* -- highlighting ----------------------------------------------------- */

    function requestHighlight() {
      var value = editor.value;
      var mySeq = ++state.seq;
      if (state.controller) {
        state.controller.abort(); // drop the previous in-flight request
      }
      var controller = new AbortController();
      state.controller = controller;
      fetch(highlightUrl + "?q=" + encodeURIComponent(value), {
        credentials: "same-origin",
        signal: controller.signal,
      })
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          // Ignore out-of-order replies and replies for text the user has
          // since edited away, so the overlay always matches the textarea.
          if (mySeq !== state.seq || editor.value !== value) {
            return;
          }
          renderSpans(overlay, data.spans || []);
          syncScroll();
        })
        .catch(function () {
          // Abort or network failure: the optimistic plain render already
          // shows the correct text, so typing is never blocked. Offline just
          // means no colors until the next successful fetch.
        });
    }

    var debounceTimer = null;
    function scheduleHighlight() {
      // SPIKE: a single trailing-edge debounce. A burst of keystrokes issues
      // one request on the pause; each new keystroke also aborts any request
      // still in flight, so at most one round-trip is outstanding.
      if (debounceTimer) {
        clearTimeout(debounceTimer);
      }
      debounceTimer = setTimeout(requestHighlight, DEBOUNCE_MS);
    }

    /* -- scroll / caret sync --------------------------------------------- */

    function syncScroll() {
      // SPIKE: keep the overlay aligned with the textarea's horizontal scroll.
      // wrap="off" + white-space:pre makes both scroll identically; we mirror
      // the offset on every scroll/input so the caret sits over its glyph.
      overlay.scrollLeft = editor.scrollLeft;
      overlay.scrollTop = editor.scrollTop;
    }

    /* -- autocomplete dropdown ------------------------------------------- */

    function closeDropdown() {
      dropdown.hidden = true;
      dropdown.textContent = "";
      state.items = [];
      state.active = -1;
      editor.setAttribute("aria-expanded", "false");
    }

    function openDropdown(items) {
      state.items = items;
      state.active = -1;
      dropdown.textContent = "";
      for (var i = 0; i < items.length; i++) {
        var li = document.createElement("li");
        li.className = "dsq-option";
        li.setAttribute("role", "option");
        li.textContent = items[i].label;
        (function (index) {
          li.addEventListener("mousedown", function (ev) {
            ev.preventDefault(); // keep focus in the textarea
            acceptSuggestion(index);
          });
        })(i);
        dropdown.appendChild(li);
      }
      dropdown.hidden = false;
      editor.setAttribute("aria-expanded", "true");
    }

    function refreshDropdown() {
      if (!tokensUrl) {
        return;
      }
      var token = caretToken(editor.value, editor.selectionStart);
      if (!token.text) {
        closeDropdown();
        return;
      }
      var items = suggestionsFor(token, state.schema);
      if (!items.length) {
        closeDropdown();
        return;
      }
      openDropdown(items);
    }

    function paintActive() {
      var options = dropdown.children;
      for (var i = 0; i < options.length; i++) {
        options[i].classList.toggle("dsq-option--active", i === state.active);
      }
    }

    function moveActive(delta) {
      if (!state.items.length) {
        return;
      }
      state.active =
        (state.active + delta + state.items.length) % state.items.length;
      paintActive();
    }

    function acceptSuggestion(index) {
      var item = state.items[index];
      if (!item) {
        return;
      }
      var value = editor.value;
      var caret = editor.selectionStart;
      var token = caretToken(value, caret);
      var before = value.slice(0, token.start);
      var after = value.slice(caret);
      editor.value = before + item.insert + after;
      var newCaret = before.length + item.insert.length;
      editor.setSelectionRange(newCaret, newCaret);
      closeDropdown();
      renderPlain(overlay, editor.value);
      syncScroll();
      scheduleHighlight();
      refreshDropdown();
    }

    /* -- events ----------------------------------------------------------- */

    editor.addEventListener("input", function () {
      renderPlain(overlay, editor.value); // text is never stale, only color
      syncScroll();
      scheduleHighlight();
      refreshDropdown();
    });

    editor.addEventListener("scroll", syncScroll);

    editor.addEventListener("keydown", function (ev) {
      var open = !dropdown.hidden;
      if (ev.key === "ArrowDown" && open) {
        ev.preventDefault();
        moveActive(1);
      } else if (ev.key === "ArrowUp" && open) {
        ev.preventDefault();
        moveActive(-1);
      } else if (ev.key === "Enter") {
        // SPIKE: Enter is overloaded. With an active suggestion it accepts;
        // otherwise it must submit the form, because a bare Enter in a
        // textarea would insert a newline instead of searching.
        if (open && state.active >= 0) {
          ev.preventDefault();
          acceptSuggestion(state.active);
        } else {
          ev.preventDefault();
          closeDropdown();
          if (form) {
            form.requestSubmit ? form.requestSubmit() : form.submit();
          }
        }
      } else if (ev.key === "Escape" && open) {
        ev.preventDefault();
        closeDropdown();
      }
    });

    editor.addEventListener("blur", function () {
      // Delay so a mousedown on an option is processed before we hide it.
      setTimeout(closeDropdown, 120);
    });

    // Initial paint: show the server's colors for any pre-filled ?q= value.
    renderPlain(overlay, editor.value);
    if (editor.value) {
      requestHighlight();
    }
  }

  function init() {
    var inputs = document.querySelectorAll("input[data-dsq-search]");
    for (var i = 0; i < inputs.length; i++) {
      enhance(inputs[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
