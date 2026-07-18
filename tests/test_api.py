from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models import SearchResponse, SearchResult
from app.search import _format_context_text, _normalize_hit


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_normalize_hit_maps_ddgs_fields() -> None:
    item = _normalize_hit(
        {"title": "Example", "href": "https://example.com", "body": "A snippet"}
    )
    assert item is not None
    assert item.title == "Example"
    assert item.url == "https://example.com"
    assert item.snippet == "A snippet"


def test_format_context_text() -> None:
    text = _format_context_text(
        [
            SearchResult(
                title="One",
                url="https://one.example",
                snippet="First",
            )
        ]
    )
    assert "1. One" in text
    assert "First" in text
    assert "https://one.example" in text


def test_v1_search_validation() -> None:
    response = client.post("/v1/search", json={"query": "", "max_results": 5})
    assert response.status_code == 422


def test_v1_search_success() -> None:
    fake = SearchResponse(
        matched=True,
        query="python",
        results=[
            SearchResult(
                title="Python.org",
                url="https://www.python.org/",
                snippet="Official Python site",
            )
        ],
        context_text="1. Python.org\nOfficial Python site\nSource: https://www.python.org/",
        provider="duckduckgo",
    )
    with patch("app.main.search", return_value=fake) as mocked:
        response = client.post(
            "/v1/search",
            json={"query": "python", "max_results": 3},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["matched"] is True
    assert data["query"] == "python"
    assert data["provider"] == "duckduckgo"
    assert len(data["results"]) == 1
    assert data["results"][0]["title"] == "Python.org"
    assert data["results"][0]["url"] == "https://www.python.org/"
    assert data["results"][0]["snippet"] == "Official Python site"
    assert data["context_text"]
    mocked.assert_awaited_once()


def test_v1_search_auth_when_configured(monkeypatch) -> None:
    monkeypatch.setattr("app.auth.settings.api_key", "secret-token")
    response = client.post("/v1/search", json={"query": "test", "max_results": 1})
    assert response.status_code == 401

    fake = SearchResponse(matched=False, query="test", provider="duckduckgo", error="no_results")
    with patch("app.main.search", return_value=fake):
        ok = client.post(
            "/v1/search",
            json={"query": "test", "max_results": 1},
            headers={"Authorization": "Bearer secret-token"},
        )
    assert ok.status_code == 200
