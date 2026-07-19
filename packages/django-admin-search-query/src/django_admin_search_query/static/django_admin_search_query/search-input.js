/*
 * django-admin-search-query: client-highlighted colored search input.
 *
 * Strategy: highlighting is CLIENT-side. `search-lexer.js` ports the Python
 * lexer to JS, so the overlay recolors synchronously on every keystroke with
 * no per-edit network round-trip -- the typing stagger is gone.
 *
 * The stock admin `<input id=searchbar>` is enhanced into a native
 * `<input class=dsq-editor>` (transparent text, visible caret) layered over an
 * `aria-hidden` mirror `<div class=dsq-mirror>` that paints role-classed
 * spans. Box metrics are copied from the live `#searchbar` so the editor is
 * pixel-identical to Django's themed input; an `<input>`'s auto height equals
 * a one-line `<div>`'s once font/line-height/padding/border match, so height
 * and alignment fix themselves.
 *
 * A hand-rolled combobox (faithful to @github/combobox-nav) drives a
 * keyboard-navigable listbox: DOM focus never leaves the input, navigation is
 * `aria-activedescendant`, and commits arrive as a `combobox-commit` event the
 * widget handles by splicing the active token in place.
 *
 * With JavaScript off, the original `<input name=q>` still submits `?q=`.
 */
(function () {
  "use strict";

  var Lexer = window.DSQLexer;
  var SUGGEST_DEBOUNCE_MS = 150;

  /* ---- token-endpoint schema cache (one fetch per URL, shared) ---------- */

  var schemaCache = Object.create(null);

  function loadSchema(url) {
    if (!schemaCache[url]) {
      schemaCache[url] = fetch(url, { credentials: "same-origin" })
        .then(function (response) {
          return response.ok ? response.json() : { fields: [], default_fields: [] };
        })
        .catch(function () {
          return { fields: [], default_fields: [] };
        });
    }
    return schemaCache[url];
  }

  /* ---- metrics: make editor + mirror pixel-identical to #searchbar ------ */

  // Geometry copied to BOTH editor and mirror so their content boxes coincide.
  // These -- not any hard-coded CSS -- drive height and alignment, which is why
  // the shared CSS rule carries no font-size/padding/line-height.
  var GEOMETRY_PROPS = [
    "fontFamily",
    "fontSize",
    "fontWeight",
    "fontStyle",
    "fontVariant",
    "letterSpacing",
    "wordSpacing",
    "lineHeight",
    "textIndent",
    "textTransform",
    "paddingTop",
    "paddingRight",
    "paddingBottom",
    "paddingLeft",
    "borderTopWidth",
    "borderRightWidth",
    "borderBottomWidth",
    "borderLeftWidth",
    "boxSizing",
    "width",
  ];

  function copyGeometry(computed, target) {
    for (var i = 0; i < GEOMETRY_PROPS.length; i++) {
      target.style[GEOMETRY_PROPS[i]] = computed[GEOMETRY_PROPS[i]];
    }
  }

  /* ---- overlay rendering (synchronous, no wipe) ------------------------- */

  // Repaint the mirror from client-lexed spans. Because coloring is local we
  // rebuild in one pass on the same tick as the keystroke -- there is never an
  // intermediate un-colored "plain" state to flicker through.
  function renderSpans(mirror, spans) {
    mirror.textContent = "";
    for (var i = 0; i < spans.length; i++) {
      var span = spans[i];
      var el = document.createElement("span");
      el.className = "dsq-token dsq-token--" + span.role;
      el.textContent = span.text;
      mirror.appendChild(el);
    }
    // A trailing zero-width char keeps a final space measurable for scroll sync
    // and the mirror non-empty (so it holds full height) when the value is "".
    mirror.appendChild(document.createTextNode("​"));
  }

  /* ---- caret-context parsing for autocomplete (NOT query parsing) ------- */

  // The maximal non-whitespace run the caret sits in, with both offsets so a
  // commit can splice it by (start, end) without rebuilding the whole string.
  function activeToken(value, caret) {
    var start = caret;
    while (start > 0 && !/\s/.test(value[start - 1])) {
      start -= 1;
    }
    var end = caret;
    while (end < value.length && !/\s/.test(value[end])) {
      end += 1;
    }
    return { start: start, end: end, text: value.slice(start, caret) };
  }

  function fieldByNameOrAlias(schema, name) {
    var fields = (schema && schema.fields) || [];
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

  // Token-under-caret picks the mode: enum-value after `enumfield:`, else
  // field-name on a bare prefix. Returns {mode, field, fragment} so the
  // suggestion source can be swapped for a server without touching callers.
  function contextFor(token) {
    var colon = token.text.indexOf(":");
    if (colon >= 0) {
      return {
        mode: "enum-value",
        field: token.text.slice(0, colon).replace(/^[-+]/, ""),
        fragment: token.text.slice(colon + 1),
      };
    }
    return {
      mode: "field-name",
      field: null,
      fragment: token.text.replace(/^[-+]/, ""),
    };
  }

  // Resolve a context to suggestion items. Local today (field names, operators,
  // and enum values all live in the cached schema); the (mode, field, fragment)
  // shape is exactly what a future `search-suggest/?field=&q=` endpoint takes.
  function localSuggestions(context, schema) {
    if (context.mode === "enum-value") {
      var spec = fieldByNameOrAlias(schema, context.field);
      if (!spec) {
        return [];
      }
      var fragment = context.fragment;
      var operators = spec.operators || [];
      var enumValues = spec.enum_values || [];
      // Operator mode: the fragment already opens an operator (`>`/`<`/`[`/`{`),
      // or a comparison/range field with no enum has only operators to offer.
      // Otherwise complete against the enum values.
      var startsOperator = /^[<>[{]/.test(fragment);
      var source =
        operators.length && (startsOperator || (fragment === "" && !enumValues.length))
          ? operators
          : enumValues;
      return source
        .filter(function (candidate) {
          // Drop the exact fragment so a fully-typed value/operator closes the
          // list instead of re-offering itself.
          return candidate.indexOf(fragment) === 0 && candidate !== fragment;
        })
        .map(function (candidate) {
          var text = context.field + ":" + candidate;
          return { label: text, insert: text };
        });
    }
    return ((schema && schema.fields) || [])
      .filter(function (field) {
        return field.name.indexOf(context.fragment) === 0;
      })
      .map(function (field) {
        return { label: field.name + ":", insert: field.name + ":" };
      });
  }

  // Debounced, abortable suggestion controller. The source is local now, but
  // the debounce + AbortController + (field, fragment) cache are here so a
  // server-backed field drops in with no call-site change. `AbortError` is
  // guarded, never surfaced as a failure.
  function createSuggestionController(getSchema) {
    var cache = Object.create(null);
    var timer = null;
    var controller = null;

    function key(context) {
      return context.mode + "\u0000" + context.field + "\u0000" + context.fragment;
    }

    function request(context) {
      if (timer) {
        clearTimeout(timer);
      }
      if (controller) {
        controller.abort();
        controller = null;
      }
      var cached = cache[key(context)];
      if (cached) {
        return Promise.resolve(cached);
      }
      controller = new AbortController();
      var signal = controller.signal;
      return new Promise(function (resolve, reject) {
        timer = setTimeout(function () {
          if (signal.aborted) {
            reject(new DOMException("aborted", "AbortError"));
            return;
          }
          // Swap this line for `fetch(url, {signal}).then(r => r.json())`
          // when a field is server-backed; everything else already handles it.
          var items = localSuggestions(context, getSchema());
          cache[key(context)] = items;
          resolve(items);
        }, SUGGEST_DEBOUNCE_MS);
      });
    }

    return { request: request };
  }

  /* ---- hand-rolled combobox (faithful to @github/combobox-nav) ---------- */

  // ~150 LOC of the combobox-nav contract: aria-activedescendant navigation
  // with DOM focus never leaving the input, role=option + unique id +
  // aria-selected on the active option only, scrollIntoView, and a
  // `combobox-commit` event the consumer handles (this class never mutates
  // input.value). start()/stop() are gated on the listbox being open.
  function Combobox(input, list) {
    this.input = input;
    this.list = list;
    this.isComposing = false;
    this.started = false;
    var self = this;
    this.onKeydown = function (event) {
      keyboardBindings(event, self);
    };
    this.onComposition = function (event) {
      self.isComposing = event.type === "compositionstart";
      if (self.isComposing) {
        self.clearSelection();
      }
    };
    this.onClick = function (event) {
      commitWithElement(event);
    };
    input.setAttribute("role", "combobox");
    input.setAttribute("aria-controls", list.id);
    input.setAttribute("aria-expanded", "false");
    input.setAttribute("aria-autocomplete", "list");
    input.setAttribute("aria-haspopup", "listbox");
  }

  Combobox.prototype.start = function () {
    if (this.started) {
      return;
    }
    this.started = true;
    this.input.setAttribute("aria-expanded", "true");
    this.input.addEventListener("compositionstart", this.onComposition);
    this.input.addEventListener("compositionend", this.onComposition);
    this.input.addEventListener("keydown", this.onKeydown);
    this.list.addEventListener("click", this.onClick);
  };

  Combobox.prototype.stop = function () {
    if (!this.started) {
      return;
    }
    this.started = false;
    this.clearSelection();
    this.input.setAttribute("aria-expanded", "false");
    this.input.removeEventListener("compositionstart", this.onComposition);
    this.input.removeEventListener("compositionend", this.onComposition);
    this.input.removeEventListener("keydown", this.onKeydown);
    this.list.removeEventListener("click", this.onClick);
  };

  Combobox.prototype.options = function () {
    return Array.prototype.slice.call(this.list.querySelectorAll('[role="option"]'));
  };

  Combobox.prototype.selectedIndex = function () {
    var options = this.options();
    for (var i = 0; i < options.length; i++) {
      if (options[i].getAttribute("aria-selected") === "true") {
        return i;
      }
    }
    return -1;
  };

  Combobox.prototype.navigate = function (delta) {
    var options = this.options();
    if (!options.length) {
      return;
    }
    var current = this.selectedIndex();
    var next;
    if (current < 0) {
      next = delta === 1 ? 0 : options.length - 1;
    } else {
      next = current + delta;
      if (next < 0 || next >= options.length) {
        // At the ends, hand focus back to the bare input (nothing selected),
        // matching combobox-nav rather than wrapping around.
        this.clearSelection();
        return;
      }
    }
    this.selectOption(options, next);
  };

  Combobox.prototype.selectAt = function (index) {
    var options = this.options();
    if (index >= 0 && index < options.length) {
      this.selectOption(options, index);
    }
  };

  Combobox.prototype.selectOption = function (options, index) {
    for (var i = 0; i < options.length; i++) {
      var option = options[i];
      if (i === index) {
        option.setAttribute("aria-selected", "true");
        this.input.setAttribute("aria-activedescendant", option.id);
        option.scrollIntoView({ block: "nearest", inline: "nearest" });
      } else {
        option.removeAttribute("aria-selected");
      }
    }
  };

  Combobox.prototype.clearSelection = function () {
    this.input.removeAttribute("aria-activedescendant");
    var options = this.options();
    for (var i = 0; i < options.length; i++) {
      options[i].removeAttribute("aria-selected");
    }
  };

  Combobox.prototype.commit = function () {
    var target = this.list.querySelector('[role="option"][aria-selected="true"]');
    if (!target) {
      return false;
    }
    fireCommit(target);
    return true;
  };

  function keyboardBindings(event, combobox) {
    // Ignore modified chords (incl. the macOS Ctrl-n/p bindings we don't need)
    // and any key pressed mid-IME-composition.
    if (event.shiftKey || event.metaKey || event.altKey || event.ctrlKey) {
      return;
    }
    if (combobox.isComposing) {
      return;
    }
    switch (event.key) {
      case "Enter":
        if (combobox.commit()) {
          event.preventDefault();
        }
        break;
      case "Tab":
        if (combobox.commit()) {
          event.preventDefault();
        }
        break;
      case "Escape":
        combobox.input.dispatchEvent(new CustomEvent("combobox-cancel"));
        event.preventDefault();
        break;
      case "ArrowDown":
        combobox.navigate(1);
        event.preventDefault();
        break;
      case "ArrowUp":
        combobox.navigate(-1);
        event.preventDefault();
        break;
      case "Home":
        combobox.selectAt(0);
        event.preventDefault();
        break;
      case "End":
        combobox.selectAt(combobox.options().length - 1);
        event.preventDefault();
        break;
      default:
        break;
    }
  }

  function commitWithElement(event) {
    var target = event.target.closest ? event.target.closest('[role="option"]') : null;
    if (!target) {
      return;
    }
    fireCommit(target);
  }

  function fireCommit(target) {
    target.dispatchEvent(new CustomEvent("combobox-commit", { bubbles: true }));
  }

  /* ---- the widget -------------------------------------------------------- */

  var comboSeq = 0;

  function enhance(input, tokensUrl) {
    if (!Lexer) {
      return; // lexer asset missing: leave stock admin search untouched
    }

    // Read the themed metrics while #searchbar is still visible in the flow.
    var computed = window.getComputedStyle(input);
    var searchbarColor = computed.color;
    var searchbarBackground = computed.backgroundColor;
    var searchbarBorderColor = computed.borderTopColor;
    var searchbarBorderStyle = computed.borderTopStyle;

    var wrap = document.createElement("div");
    wrap.className = "dsq-wrap";

    var mirror = document.createElement("div");
    mirror.className = "dsq-mirror";
    mirror.setAttribute("aria-hidden", "true");

    var editor = document.createElement("input");
    editor.type = "text";
    editor.className = "dsq-editor";
    editor.name = input.name || "q";
    editor.value = input.value;
    editor.setAttribute("autocomplete", "off");
    editor.setAttribute("autocapitalize", "off");
    editor.setAttribute("autocorrect", "off");
    editor.setAttribute("spellcheck", "false");
    if (input.getAttribute("placeholder")) {
      editor.setAttribute("placeholder", input.getAttribute("placeholder"));
    }
    if (input.getAttribute("aria-describedby")) {
      editor.setAttribute("aria-describedby", input.getAttribute("aria-describedby"));
    }

    var listbox = document.createElement("ul");
    listbox.className = "dsq-listbox";
    listbox.id = "dsq-listbox-" + ++comboSeq;
    listbox.setAttribute("role", "listbox");
    listbox.setAttribute("aria-label", "Search suggestions");
    listbox.hidden = true;

    copyGeometry(computed, editor);
    copyGeometry(computed, mirror);
    // Overlay trick: mirror carries the real background + colors; the editor
    // sits on top with transparent text and background, its border/caret themed
    // from #searchbar so it reads as the native input.
    mirror.style.background = searchbarBackground;
    mirror.style.color = searchbarColor;
    editor.style.borderStyle = searchbarBorderStyle;
    editor.style.borderColor = searchbarBorderColor;
    editor.style.caretColor = searchbarColor;
    // Force the overlay-critical transparency inline. Admin base.css styles
    // `input[type=text]` (specificity 0,0,1,1) with an opaque `background-color`
    // and a themed `color`, outranking the `.dsq-editor` class rule (0,0,1,0) --
    // the editor would otherwise paint over the mirror behind it. Inline styles
    // outrank any selector, so this also survives themed admins.
    editor.style.background = "transparent";
    editor.style.color = "transparent";
    editor.style.webkitTextFillColor = "transparent";

    wrap.appendChild(mirror);
    wrap.appendChild(editor);
    wrap.appendChild(listbox);

    // Neutralize (don't destroy) the stock #searchbar: keep it in the DOM but
    // inert and non-submitting so JS-off still submits the plain input. The
    // editor becomes the sole `?q=` submitter.
    input.removeAttribute("name");
    input.hidden = true;
    input.tabIndex = -1;
    input.setAttribute("aria-hidden", "true");
    // Move the stock input's id onto the editor so the admin's
    // `<label for="searchbar">` names the real combobox. Without this the
    // enhanced input has no accessible name (WCAG 4.1.2 / 1.3.1); the transient
    // duplicate id is gone by the next statement, before any AT query.
    if (input.id) {
      editor.id = input.id;
      input.removeAttribute("id");
    }
    input.parentNode.insertBefore(wrap, input.nextSibling);

    var state = { schema: { fields: [], default_fields: [] } };
    var suggestions = createSuggestionController(function () {
      return state.schema;
    });
    var combobox = new Combobox(editor, listbox);

    if (tokensUrl) {
      loadSchema(tokensUrl).then(function (schema) {
        state.schema = schema;
        recolor();
      });
    }

    /* -- highlighting: synchronous, client-side --------------------------- */

    function recolor() {
      var spans = Lexer.highlightQuerySpans(editor.value);
      spans = Lexer.applyRegistryErrors(spans, state.schema);
      renderSpans(mirror, spans);
      syncScroll();
    }

    function syncScroll() {
      // Single line: mirror only tracks horizontal scroll (drop scrollTop).
      mirror.scrollLeft = editor.scrollLeft;
    }

    /* -- suggestions listbox ---------------------------------------------- */

    function closeList() {
      combobox.stop();
      listbox.hidden = true;
      listbox.textContent = "";
    }

    function openList(items) {
      listbox.textContent = "";
      for (var i = 0; i < items.length; i++) {
        var option = document.createElement("li");
        option.className = "dsq-option";
        option.id = listbox.id + "-opt-" + i;
        option.setAttribute("role", "option");
        option.dataset.insert = items[i].insert;
        option.textContent = items[i].label;
        listbox.appendChild(option);
      }
      listbox.hidden = false;
      combobox.start();
    }

    function refreshList() {
      if (!tokensUrl) {
        return;
      }
      var token = activeToken(editor.value, editor.selectionStart);
      if (!token.text) {
        closeList();
        return;
      }
      var context = contextFor(token);
      suggestions
        .request(context)
        .then(function (items) {
          // Ignore a stale resolution: the caret may have moved on.
          var fresh = activeToken(editor.value, editor.selectionStart);
          if (fresh.text !== token.text || fresh.start !== token.start) {
            return;
          }
          if (!items.length) {
            closeList();
            return;
          }
          openList(items);
        })
        .catch(function (error) {
          if (error && error.name === "AbortError") {
            return; // expected when a newer keystroke supersedes this request
          }
          closeList();
        });
    }

    // Commit: splice the ACTIVE token by offsets, never rebuild the string.
    function commitOption(option) {
      var chosen = option.dataset.insert;
      var value = editor.value;
      var token = activeToken(value, editor.selectionStart);
      editor.value = value.slice(0, token.start) + chosen + value.slice(token.end);
      var caret = token.start + chosen.length;
      editor.setSelectionRange(caret, caret);
      closeList();
      recolor();
      refreshList();
    }

    /* -- events ----------------------------------------------------------- */

    editor.addEventListener("input", function () {
      recolor();
      refreshList();
    });

    editor.addEventListener("scroll", syncScroll);

    editor.addEventListener("click", refreshList);

    listbox.addEventListener("combobox-commit", function (event) {
      commitOption(event.target);
    });

    editor.addEventListener("combobox-cancel", closeList);

    listbox.addEventListener("mousedown", function (event) {
      // Keep DOM focus in the editor when an option is clicked, so the commit
      // splice and caret placement land on a still-focused input.
      event.preventDefault();
    });

    editor.addEventListener("blur", function () {
      // Delay so a click on an option is handled before the list hides.
      setTimeout(closeList, 120);
    });

    // Keep the mirror pixel-locked to the editor as its box changes (zoom,
    // responsive width, late web-font load).
    if (typeof ResizeObserver !== "undefined") {
      new ResizeObserver(function () {
        copyGeometry(window.getComputedStyle(editor), mirror);
        syncScroll();
      }).observe(editor);
    }

    recolor();
  }

  function init() {
    // The config element (from the non-forking change_list template) carries
    // the token endpoint URL; enhance the stock admin #searchbar in place.
    var configs = document.querySelectorAll("[data-dsq-search]");
    for (var i = 0; i < configs.length; i++) {
      var input = document.getElementById("searchbar");
      if (input) {
        enhance(input, configs[i].dataset.searchTokensUrl);
      }
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
