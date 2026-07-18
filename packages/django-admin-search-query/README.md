# django-admin-search-query

An optional Django admin integration built on top of
[`django-search-query`](https://pypi.org/project/django-search-query/).

It adds structured search support to Django admin pages while keeping the
underlying query language usable independently. The relationship between the
packages stays loose so the core package does not couple to Django admin
behavior or presentation concerns.

The package may also provide an optional, self-contained search input
implemented in vanilla JavaScript, offering syntax highlighting, contextual
suggestions, and semantic autocomplete while remaining usable as a normal text
field when JavaScript is unavailable or disabled.

> [!NOTE]
> Early scaffolding. The admin mixin and the JavaScript input are not
> implemented yet.

## Install

Installing the admin integration pulls in the core query language:

```console
$ pip install django-admin-search-query
```

## Supported versions

- Python 3.12+
- Django 5.2 (LTS) and 6.0

## Documentation

https://django-search-query.git-pull.com
