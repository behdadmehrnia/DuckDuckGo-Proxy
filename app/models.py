from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Body expected by YarKids ``POST {WEB_SEARCH_API_URL}/v1/search``."""

    query: str = Field(..., min_length=1, description="Search query string")
    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of results to return (clamped 1–10, matching YarKids)",
    )


class SearchResult(BaseModel):
    title: str = ""
    url: str | None = None
    snippet: str = ""


class SearchResponse(BaseModel):
    """Shape consumed by YarKids ``_parse_external_web_search_payload``."""

    matched: bool = False
    query: str | None = None
    results: list[SearchResult] = Field(default_factory=list)
    context_text: str | None = None
    provider: str = "duckduckgo"
    error: str | None = None
