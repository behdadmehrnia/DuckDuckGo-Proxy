from __future__ import annotations

import asyncio
from typing import Any

from ddgs import DDGS
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException

from app.config import settings
from app.models import SearchResponse, SearchResult


def _format_context_text(results: list[SearchResult]) -> str:
    lines: list[str] = []
    for idx, item in enumerate(results, start=1):
        title = item.title.strip() or f"Result {idx}"
        snippet = item.snippet.strip()
        url = (item.url or "").strip()
        block = f"{idx}. {title}"
        if snippet:
            block = f"{block}\n{snippet}"
        if url:
            block = f"{block}\nSource: {url}"
        lines.append(block)
    return "\n\n".join(lines)


def _normalize_hit(raw: dict[str, Any]) -> SearchResult | None:
    title = str(raw.get("title") or raw.get("name") or "").strip()
    snippet = str(
        raw.get("body")
        or raw.get("snippet")
        or raw.get("content")
        or raw.get("description")
        or ""
    ).strip()
    url_raw = raw.get("href") or raw.get("url") or raw.get("link")
    url = str(url_raw).strip() if url_raw else None
    if not (title or snippet):
        return None
    return SearchResult(title=title, url=url, snippet=snippet)


def _search_sync(query: str, max_results: int) -> SearchResponse:
    cleaned = query.strip()
    if not cleaned:
        return SearchResponse(
            matched=False,
            query=query,
            provider="duckduckgo",
            error="empty_query",
        )

    max_results = max(1, min(int(max_results), 10))

    try:
        with DDGS(
            timeout=settings.search_timeout_sec,
            verify=settings.verify_ssl,
        ) as ddgs:
            hits = list(
                ddgs.text(
                    cleaned,
                    region=settings.region,
                    safesearch=settings.safesearch,
                    max_results=max_results,
                    backend=settings.backend_list,
                )
            )
    except RatelimitException:
        return SearchResponse(
            matched=False,
            query=cleaned,
            provider="duckduckgo",
            error="rate_limited",
        )
    except TimeoutException:
        return SearchResponse(
            matched=False,
            query=cleaned,
            provider="duckduckgo",
            error="timeout",
        )
    except DDGSException as exc:
        return SearchResponse(
            matched=False,
            query=cleaned,
            provider="duckduckgo",
            error=f"search_failed: {exc}",
        )
    except Exception as exc:  # noqa: BLE001 — surface unexpected upstream errors cleanly
        return SearchResponse(
            matched=False,
            query=cleaned,
            provider="duckduckgo",
            error=f"{type(exc).__name__}: {exc}",
        )

    results: list[SearchResult] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        item = _normalize_hit(hit)
        if item:
            results.append(item)
        if len(results) >= max_results:
            break

    if not results:
        return SearchResponse(
            matched=False,
            query=cleaned,
            results=[],
            provider="duckduckgo",
            error="no_results",
        )

    return SearchResponse(
        matched=True,
        query=cleaned,
        results=results,
        context_text=_format_context_text(results),
        provider="duckduckgo",
    )


async def search(query: str, max_results: int) -> SearchResponse:
    return await asyncio.to_thread(_search_sync, query, max_results)
