# CLAUDE.md — Development Guide for AI Assistants

This file provides context for Claude Code and other AI assistants working on this repository.

## Project Overview

This is a **Model Context Protocol (MCP) server** that connects to the **Gainsight Customer Communities** (formerly inSided) REST API. It exposes 15 read-only tools that let AI assistants search and browse community content.

This is a third-party, community-built integration — not officially affiliated with Gainsight.

## Architecture

```
src/
├── client.py    # GainsightClient — async HTTP client with OAuth2
├── server.py    # FastMCP server — tool definitions and entry point
├── __main__.py  # Allows `python -m src` invocation
└── __init__.py
```

- **`client.py`** handles all HTTP communication with the Gainsight API. It manages OAuth2 token acquisition (with `scope=read`), caching (with 60s pre-expiry refresh), and provides typed async methods for each API endpoint. The `CONTENT_TYPE_PATHS` mapping translates content types to their API path segments.
- **`server.py`** defines 15 MCP tools using the `FastMCP` framework. Each tool function calls the client, transforms parameters, and returns JSON strings. A lazy-initialized module-level `_client` singleton is used.

## Key Design Decisions

- **Read-only by design**: All tools use `scope=read` — no write operations are exposed, making it safe to share with AI agents.
- **Lazy client initialization**: The `GainsightClient` is created on first tool call, not at import time. This allows the module to be imported and tested without requiring environment variables.
- **Token caching**: OAuth2 tokens are reused until 60 seconds before expiry to minimize auth requests.
- **Token scope**: The token request must include `scope=read` — without it, the token is issued but API endpoints return 401.
- **Parameter cleaning**: The `_clean()` helper strips `None` values so optional params aren't sent as query strings.
- **JSON string returns**: All tools return `json.dumps()` strings — this is the expected return format for MCP tool handlers.
- **Content-type routing**: The API uses separate endpoints per content type (e.g. `/v2/questions`, `/v2/ideas`). The `list_topics` tool routes to the correct endpoint based on the `content_type` parameter. The `get_topic` tool looks up the content type first, then fetches detail + replies from the type-specific endpoint.
- **Pagination uses `pageSize` and `page`**: The API ignores standard names like `limit`, `offset`, `page_size`. The server translates `page_size` to `pageSize` for the user.
- **Date range filters**: The `createdAt` and `lastActivity` API params accept JSON objects with `from`/`to` keys. The server tools expose these as separate `created_after`/`created_before` and `active_after`/`active_before` string params and serialise them internally.

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_community` | Full-text search with filtering (categories, content types, tags, hasAnswer) |
| `search_tags` | Search for tags by name (returns matching tags with IDs and usage counts) |
| `list_topics` | List/filter topics with rich filtering (category, tags, dates, sort, content types) |
| `get_topic` | Get full topic detail + replies by ID (auto-detects content type) |
| `list_ideas` | List feature ideas |
| `list_categories` | List all categories |
| `list_tags` | List all public tags |
| `get_category` | Get a single category by ID |
| `get_category_tree` | Get the full category hierarchy |
| `get_category_topic_counts` | Get visible topic counts per category |
| `list_topics_by_category` | List topics within a category (with filtering) |
| `list_idea_statuses` | List idea pipeline stages (e.g. "Planned", "Shipped") |
| `list_product_areas` | List product area taxonomy |
| `get_poll_results` | Get poll results for a topic |
| `get_reply` | Fetch a single reply by ID |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GS_CC_CLIENT_ID` | Yes | — | OAuth2 client ID |
| `GS_CC_CLIENT_SECRET` | Yes | — | OAuth2 client secret |
| `GS_CC_REGION` | No | `eu-west-1` | `eu-west-1` or `us-west-2` |

## API Endpoints Used

All requests go to `https://api2-{region}.insided.com`:

| Method | Path | Used By |
|--------|------|---------|
| POST | `/oauth2/token` | Token acquisition (must include `scope=read`) |
| GET | `/search` | `search_community` (dedicated Search API with filtering) |
| GET | `/search/tags` | `search_tags` |
| GET | `/v2/topics` | `list_topics` (unified with filtering), `get_topic` (ID lookup) |
| GET | `/v2/questions` | `list_topics(content_type="question")` |
| GET | `/v2/conversations` | `list_topics(content_type="conversation")` |
| GET | `/v2/articles` | `list_topics(content_type="article")` |
| GET | `/v2/ideas` | `list_ideas`, `list_topics(content_type="idea")` |
| GET | `/v2/productUpdates` | `list_topics(content_type="productUpdate")` |
| GET | `/v2/{type}s/{id}` | `get_topic` (detail) |
| GET | `/v2/{type}s/{id}/replies` | `get_topic` (replies) |
| GET | `/v2/{type}s/{id}/replies/{replyId}` | `get_reply` |
| GET | `/v2/{type}s/{id}/poll` | `get_poll_results` |
| GET | `/v2/categories` | `list_categories` |
| GET | `/v2/categories/{id}` | `get_category` |
| GET | `/v2/category/getTree` | `get_category_tree` |
| GET | `/v2/categories/getVisibleTopicsCount` | `get_category_topic_counts` |
| GET | `/v2/categories/{id}/topics` | `list_topics_by_category` |
| GET | `/v2/tags` | `list_tags` |
| GET | `/v2/moderatorTags` | Available via client (`list_moderator_tags`) |
| GET | `/v2/ideas/ideaStatuses` | `list_idea_statuses` |
| GET | `/v2/productAreas` | `list_product_areas` |

### Pagination

- Use `pageSize` (camelCase) and `page` (1-indexed) query params.
- Default page size is 25 if not specified.
- Standard names (`limit`, `offset`, `page_size`) are silently ignored by the API.

### Filtering (unified /v2/topics endpoint)

The `list_topics` tool (without `content_type`) and `list_topics_by_category` support:
- `categoryIds` — comma-separated category IDs
- `tags` / `moderatorTags` — comma-separated tag names
- `contentTypes` — comma-separated content types (e.g. `"question,idea"`)
- `sort` — sort field (e.g. `"createdAt"`, `"lastActivity"`) in descending order
- `createdAt` / `lastActivity` — JSON objects with `from`/`to` ISO date strings

### Response Format

Most `/v2/` list endpoints return `{"result": [...]}`. Replies also include `{"_metadata": {"totalCount": N, "limit": N, "offset": N}}`.

The dedicated Search API (`/search`) returns `{"community": [...]}`. The tag search (`/search/tags`) returns `{"tags": [...]}`.

## Development Commands

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_client.py
pytest tests/test_server.py
```

## Testing Strategy

- **`tests/test_client.py`** — Tests the HTTP client using `respx` to mock all outbound HTTP requests. Verifies OAuth2 flow (including `scope=read`), token caching, each API method, and error cases.
- **`tests/test_server.py`** — Tests the MCP tool functions by patching the module-level `_client` with `unittest.mock.AsyncMock`. Verifies parameter transformation, content-type routing, date range serialisation, and response serialization.

Tests are async (using `pytest-asyncio` in auto mode) and do not require real API credentials.

## Common Tasks

### Adding a New Tool

1. Add a new async method to `GainsightClient` in `client.py` for the API endpoint.
2. Add a new `@mcp.tool()` function in `server.py` that calls the client method.
3. Add tests in both `test_client.py` (mocked HTTP) and `test_server.py` (mocked client).

### Adding a New API Region

Add the region to the `REGION_BASE_URLS` dict in `client.py`.

### Modifying OAuth2 Flow

The token logic is in `GainsightClient._ensure_token()` in `client.py`. The token is cached in `_access_token` / `_token_expires_at` instance attributes. The `scope=read` parameter is required.

## Gotchas

- **`scope=read` is required**: Without it, the token is issued but all API endpoints return 401.
- **Search API uses `/search`, not `/v2/`**: The dedicated Search API lives at `/search` and `/search/tags` (not under `/v2/`). It uses the same search algorithm as the frontend UI and supports filtering by `categoryIds`, `contentTypes`, `tags`, `moderatorTags`, and `hasAnswer`. The response format differs: `{"community": [...]}` instead of `{"result": [...]}`.
- **API paths are `/v2/...`**, not `/api/v2/...` — there is no `/api` prefix.
- **Content types have separate endpoints**: `/v2/topics` returns all types but doesn't support type filtering. Use `/v2/questions`, `/v2/ideas`, etc. for type-specific listing.
- **Topic detail requires content type**: There is no `/v2/topics/{id}` — you must use `/v2/questions/{id}`, `/v2/articles/{id}`, etc. The `get_topic` tool handles this by looking up the topic first.
- **Category tree uses singular path**: `GET /v2/category/getTree` (not `/v2/categories/getTree`).
- **Pagination param is `pageSize`** (camelCase), not `page_size`. The server maps this for the user.
- **Date range params are JSON objects**: The API expects `createdAt={"from":"...","to":"..."}` as a JSON string in the query param. The server tools handle this serialisation.
- The `mcp` package `FastMCP` constructor uses `instructions=` not `description=` for the server description.
- The Hatch build requires `[tool.hatch.build.targets.wheel] packages = ["src"]` because the package name doesn't match the directory name.
- `pytest-asyncio` must be configured with `asyncio_mode = "auto"` in `pyproject.toml` for async tests to be discovered correctly.
- The Dockerfile copies `pyproject.toml` and `src/` — if you add data files or config outside those paths, update the Dockerfile.
