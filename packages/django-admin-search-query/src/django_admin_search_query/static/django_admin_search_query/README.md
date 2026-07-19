# Colored search input assets

Static assets shipped by `django_admin_search_query.mixin.SearchQueryAdminMixin`
(via its `class Media`):

- `search-input.js` — progressively enhances the admin search box into a
  textarea layered over a highlight overlay. On every edit it debounces
  (~120ms) and fetches the model's `search-highlight/` endpoint, which returns
  server-produced `(start, role, text)` spans (including a registry-aware
  `error` role). There is no JavaScript tokenizer, so the coloring cannot drift
  from the Python engine. Autocomplete data comes from the `search-tokens/`
  endpoint. With JavaScript disabled, the original `<input>` still submits
  `?q=`.
- `search-input.css` — role colors, overlay alignment, dropdown, and light/dark
  theming.
