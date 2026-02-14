# CLAUDE.md — Development Guide for AI Assistants

This file provides context for Claude Code and other AI assistants working on this repository.

## Project Overview

This is a **Model Context Protocol (MCP) server** that connects to the **Gainsight Customer Communities** (formerly inSided) REST API. It exposes five tools that let AI assistants search and browse community content.

This is a third-party, community-built integration — not officially affiliated with Gainsight.

## Architecture

```
src/
├── client.py    # GainsightClient — async HTTP client with OAuth2
├── server.py    # FastMCP server — tool definitions and entry point
├── __main__.py  # Allows `python -m src` invocation
└── __init__.py
```

- **`client.py`** handles all HTTP communication with the Gainsight API. It manages OAuth2 token acquisition, caching (with 60s pre-expiry refresh), and provides typed async methods for each API endpoint.
- **`server.py`** defines five MCP tools using the `FastMCP` framework. Each tool function calls the client, transforms parameters, and returns JSON strings. A lazy-initialized module-level `_client` singleton is used.

## Key Design Decisions

- **Lazy client initialization**: The `GainsightClient` is created on first tool call, not at import time. This allows the module to be imported and tested without requiring environment variables.
- **Token caching**: OAuth2 tokens are reused until 60 seconds before expiry to minimize auth requests.
- **Parameter cleaning**: The `_clean()` helper strips `None` values so optional params aren't sent as query strings.
- **JSON string returns**: All tools return `json.dumps()` strings — this is the expected return format for MCP tool handlers.
- **List params joined to CSV**: `content_types` and `category_ids` lists are joined with commas before being sent to the API.

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
| POST | `/oauth2/token` | Token acquisition |
| GET | `/api/v2/search` | `search_community` |
| GET | `/api/v2/topics` | `list_topics`, `list_ideas` |
| GET | `/api/v2/topics/{id}` | `get_topic` |
| GET | `/api/v2/topics/{id}/replies` | `get_topic` |
| GET | `/api/v2/categories` | `list_categories` |

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

- **`tests/test_client.py`** — Tests the HTTP client using `respx` to mock all outbound HTTP requests. Verifies OAuth2 flow, token caching, and each API method.
- **`tests/test_server.py`** — Tests the MCP tool functions by patching the module-level `_client` with `unittest.mock.AsyncMock`. Verifies parameter transformation and response serialization.

Tests are async (using `pytest-asyncio` in auto mode) and do not require real API credentials.

## Common Tasks

### Adding a New Tool

1. Add a new async method to `GainsightClient` in `client.py` for the API endpoint.
2. Add a new `@mcp.tool()` function in `server.py` that calls the client method.
3. Add tests in both `test_client.py` (mocked HTTP) and `test_server.py` (mocked client).

### Adding a New API Region

Add the region to the `REGION_BASE_URLS` dict in `client.py`.

### Modifying OAuth2 Flow

The token logic is in `GainsightClient._ensure_token()` in `client.py`. The token is cached in `_access_token` / `_token_expires_at` instance attributes.

## Gotchas

- The `mcp` package `FastMCP` constructor uses `instructions=` not `description=` for the server description.
- The Hatch build requires `[tool.hatch.build.targets.wheel] packages = ["src"]` because the package name doesn't match the directory name.
- `pytest-asyncio` must be configured with `asyncio_mode = "auto"` in `pyproject.toml` for async tests to be discovered correctly.
- The Dockerfile copies `pyproject.toml` and `src/` — if you add data files or config outside those paths, update the Dockerfile.
