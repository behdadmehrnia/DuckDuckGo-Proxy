from __future__ import annotations

from fastapi import FastAPI

from app.auth import AuthDependency
from app.config import settings
from app.models import SearchRequest, SearchResponse
from app.search import search

app = FastAPI(
    title="DuckDuckGo Search Proxy",
    description=(
        "Thin FastAPI proxy that exposes DuckDuckGo web search as "
        "``POST /v1/search`` for agentic workflows (compatible with YarKids "
        "``WEB_SEARCH_API_URL``)."
    ),
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/search", response_model=SearchResponse, dependencies=[AuthDependency])
async def v1_search(body: SearchRequest) -> SearchResponse:
    """
    Search the web and return snippets for agent context injection.

    Request body (YarKids-compatible)::

        {"query": "…", "max_results": 5}

    Response fields match what YarKids ``_parse_external_web_search_payload``
    expects: ``results[].title|url|snippet``, plus ``matched``, ``context_text``,
    ``provider``, and optional ``error``.
    """
    max_results = body.max_results or settings.default_max_results
    return await search(body.query, max_results)
