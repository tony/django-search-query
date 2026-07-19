(install)=

# Install

`django-search-query` is the core query language, independent of any particular UI, admin integration, or search backend; add it
to any Django project's environment. `django-admin-search-query` is the
optional {doc}`admin integration <packages/django-admin-search-query/index>`
built on top of it -- reach for it only when you want structured search on an
admin changelist page.

```{package-install}
```

Register whichever package you installed in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django_search_query",
    "django_admin_search_query",  # optional: admin integration
    ...
]
```

`django_admin_search_query` needs `django.contrib.admin` (and its own
dependencies, `contenttypes`, `auth`, `messages`, `sessions`) already
installed -- skip it if you only use the core query language.

(developmental-releases)=

## Developmental releases

New versions are published to PyPI as alpha, beta, or release candidates. In
their versions you will see notation like `a1`, `b1`, and `rc1`,
respectively. `1.0.0b4` would mean the 4th beta release of `1.0.0` before
general availability.

- [pip]\:

  ```console
  $ pip install --upgrade --pre django-search-query
  ```

- [pipx]\:

  ```console
  $ pipx install --suffix=@next 'django-search-query' --pip-args '\--pre' --force
  ```

- [uv]\:

  ```console
  $ uv add django-search-query --prerelease allow
  ```

- [uvx]\:

  ```console
  $ uvx --from 'django-search-query' --prerelease allow django-search-query
  ```

See {doc}`tutorial` for what to do once the package is installed.

[pip]: https://pip.pypa.io/en/stable/
[pipx]: https://pypa.github.io/pipx/docs/
[uv]: https://docs.astral.sh/uv/
[uvx]: https://docs.astral.sh/uv/guides/tools/
