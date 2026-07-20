# DuckDuckGo Search Proxy

Small FastAPI service that wraps DuckDuckGo (via [`ddgs`](https://pypi.org/project/ddgs/)) and exposes a **`POST /v1/search`** endpoint for agentic workflows.

## Endpoint

### `POST /v1/search`

**Request**

```json
{
  "query": "Minecraft 1.21 update",
  "max_results": 5
}
```

| Field | Type | Notes |
|-------|------|--------|
| `query` | string | Required |
| `max_results` | int | Optional, default `5`, clamped to `1–10` |

**Headers** (optional): `Authorization: Bearer <API_KEY>` when `API_KEY` is set.

**Response**

```json
{
  "matched": true,
  "query": "Minecraft 1.21 update",
  "results": [
    {
      "title": "…",
      "url": "https://…",
      "snippet": "…"
    }
  ],
  "context_text": "1. …\n…\nSource: https://…",
  "provider": "duckduckgo",
  "error": null
}
```

### `GET /health`

```json
{"status": "ok"}
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

```bash
curl -s http://127.0.0.1:8080/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"python asyncio","max_results":3}' | jq
```

### Docker

```bash
cp .env.example .env   # optional; edit API_KEY / VERIFY_SSL as needed
docker compose up --build -d
```

Service listens on **http://localhost:8080**.

```bash
curl -s http://localhost:8080/health
curl -s http://localhost:8080/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"python asyncio","max_results":3}'
```

Stop with `docker compose down`.

Image-only build:

```bash
docker build -t duckduckgo-proxy .
docker run --rm -p 8080:8080 -e VERIFY_SSL=true duckduckgo-proxy
```

## Configuration

| Env | Default | Description |
|-----|---------|-------------|
| `HOST` / `PORT` | `0.0.0.0` / `8080` | Bind address |
| `API_KEY` | _(empty)_ | Optional Bearer token |
| `DEFAULT_MAX_RESULTS` | `5` | Fallback when body omits max |
| `SEARCH_TIMEOUT_SEC` | `8` | Upstream search timeout |
| `SAFESEARCH` | `moderate` | `on` / `moderate` / `off` |
| `REGION` | `wt-wt` | ddgs region code |
| `BACKENDS` | `duckduckgo` | Comma-separated ddgs backends |
| `VERIFY_SSL` | `true` | Set `false` behind SSL-inspecting proxies |

## Agent / tool use

Any agent that can call HTTP tools can treat this as a search tool:

```http
POST /v1/search
Content-Type: application/json

{"query": "<user question>", "max_results": 5}
```

Use `results[].snippet` (or `context_text`) as retrieved context before answering.
