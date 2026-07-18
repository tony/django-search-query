(quickstart)=

# Quickstart

## Installation

The workspace ships two independently-installable packages.

`django-search-query` -- the core query language:

```console
$ pip install django-search-query
```

```console
$ uv add django-search-query
```

`django-admin-search-query` -- the optional Django admin integration (depends
on the core package):

```console
$ pip install django-admin-search-query
```

```console
$ uv add django-admin-search-query
```

(developmental-releases)=

### Developmental releases

New versions are published to PyPI as alpha, beta, or release candidates. In
their versions you will see notification like `a1`, `b1`, and `rc1`,
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

## Usage

```{note}
The query language and admin integration are not implemented yet. Usage
examples will land here as the packages take shape. For now, see
{doc}`packages/index` for the intended scope of each package.
```

[pip]: https://pip.pypa.io/en/stable/
[pipx]: https://pypa.github.io/pipx/docs/
[uv]: https://docs.astral.sh/uv/
[uvx]: https://docs.astral.sh/uv/guides/tools/
