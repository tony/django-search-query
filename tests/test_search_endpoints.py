"""Tests for the token and highlight admin endpoints and the enhanced input.

These are the reliable, browser-free proof for the colored input: they exercise
the server contract the JavaScript depends on (both JSON endpoints) and assert
the changelist ships the enhanced input plus its assets.
"""

from __future__ import annotations

import typing as t

import pytest
from django.urls import reverse

if t.TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from django.test import Client

TOKENS_URL = reverse("admin:test_app_article_search_tokens")
HIGHLIGHT_URL = reverse("admin:test_app_article_search_highlight")
CHANGELIST_URL = reverse("admin:test_app_article_changelist")


def _reconstruct(spans: list[dict[str, t.Any]]) -> str:
    """Concatenate span texts back into the original query string."""
    return "".join(span["text"] for span in spans)


@pytest.mark.django_db
def test_tokens_endpoint_returns_registry_schema(admin_client: Client) -> None:
    """The token endpoint exposes each field, its enum values, and defaults."""
    response = admin_client.get(TOKENS_URL)
    assert response.status_code == 200
    data = response.json()
    by_name = {field["name"]: field for field in data["fields"]}
    assert set(by_name) == {"title", "body", "author", "status", "created"}
    assert by_name["status"]["kind"] == "enum"
    assert by_name["status"]["enum_values"] == ["open", "draft", "closed"]
    assert by_name["created"]["operators"] == [">", ">=", "<", "<=", "[", "{"]
    assert data["default_fields"] == ["title", "body"]


@pytest.mark.django_db
def test_highlight_endpoint_returns_spans(admin_client: Client) -> None:
    """The highlight endpoint returns gap-free spans for a valid query."""
    response = admin_client.get(HIGHLIGHT_URL, {"q": "status:open author:tony"})
    assert response.status_code == 200
    data = response.json()
    assert _reconstruct(data["spans"]) == "status:open author:tony"
    roles = [span["role"] for span in data["spans"]]
    assert "field" in roles
    assert "error" not in roles


@pytest.mark.django_db
def test_highlight_endpoint_marks_out_of_enum_value(admin_client: Client) -> None:
    """An out-of-enum value is returned with the registry-aware ``error`` role."""
    response = admin_client.get(HIGHLIGHT_URL, {"q": "status:bogus"})
    data = response.json()
    error_spans = [span for span in data["spans"] if span["role"] == "error"]
    assert [span["text"] for span in error_spans] == ["bogus"]


@pytest.mark.django_db
def test_highlight_endpoint_marks_unknown_field(admin_client: Client) -> None:
    """An unknown field and its value both come back as ``error`` spans."""
    response = admin_client.get(HIGHLIGHT_URL, {"q": "nope:x"})
    data = response.json()
    error_texts = [span["text"] for span in data["spans"] if span["role"] == "error"]
    assert error_texts == ["nope", "x"]


@pytest.mark.django_db
def test_highlight_endpoint_handles_blank_query(admin_client: Client) -> None:
    """A missing ``q`` yields an empty span list rather than an error."""
    response = admin_client.get(HIGHLIGHT_URL)
    assert response.status_code == 200
    assert response.json()["spans"] == []


def test_endpoints_redirect_anonymous_users(client: Client) -> None:
    """The admin_view gate redirects anonymous users to the login page."""
    for url in (TOKENS_URL, HIGHLIGHT_URL):
        response = client.get(url)
        assert response.status_code == 302
        assert "/login" in response["Location"]


@pytest.mark.django_db
def test_endpoints_forbid_staff_without_view_permission(
    client: Client,
    django_user_model: type[AbstractUser],
) -> None:
    """A staff user lacking the model's view permission is denied (403)."""
    user = django_user_model.objects.create_user(
        username="staffer",
        password="pw",
        is_staff=True,
    )
    client.force_login(user)
    for url in (TOKENS_URL, HIGHLIGHT_URL):
        assert client.get(url).status_code == 403


@pytest.mark.django_db
def test_changelist_ships_enhanced_input_and_assets(admin_client: Client) -> None:
    """The changelist renders the data-hooked input and the JS/CSS assets."""
    html = admin_client.get(CHANGELIST_URL).content.decode()
    assert "data-dsq-search" in html
    assert f'data-highlight-url="{HIGHLIGHT_URL}"' in html
    assert f'data-search-tokens-url="{TOKENS_URL}"' in html
    assert "search-input.js" in html
    assert "search-input.css" in html


@pytest.mark.django_db
def test_colored_input_integration(admin_client: Client) -> None:
    """End-to-end (browser-free) proof of the whole server contract.

    Mirrors the Playwright flow without a browser: the changelist advertises
    the endpoints on the input, and both endpoints answer with the JSON the
    JavaScript consumes -- including an ``error`` span for a bad enum value.
    """
    html = admin_client.get(CHANGELIST_URL).content.decode()
    assert "data-dsq-search" in html and "search-input.js" in html

    schema = admin_client.get(TOKENS_URL).json()
    assert any(field["name"] == "status" for field in schema["fields"])

    highlighted = admin_client.get(
        HIGHLIGHT_URL,
        {"q": 'status:open author:tony "phrase" NOT status:bogus'},
    ).json()
    assert _reconstruct(highlighted["spans"]) == (
        'status:open author:tony "phrase" NOT status:bogus'
    )
    assert any(span["role"] == "error" for span in highlighted["spans"])
