# Gainsight Customer Communities MCP Server

A third-party [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for **Gainsight Customer Communities** (formerly inSided). Enables AI assistants like Claude, ChatGPT, and Cursor to search and retrieve community content through a standardised interface.

> **Note:** This is an independent, community-built integration — not officially supported by Gainsight.

## Features

- **Search** community content by keyword with filtering by category, content type, tags, and answered status
- **Search tags** by name to discover exact tag names for filtering
- **List & filter topics** by type, category, tags, date range, sort order, and more
- **Retrieve full topic details** including body content and replies
- **Browse ideas** and feature requests with vote counts
- **Explore categories** — list, get details, view hierarchy tree, and topic counts
- **View tags** and product areas for filtering and discovery
- **Check idea statuses** to understand the feature pipeline
- **Read poll results** and individual replies

All 16 tools are **read-only** — safe to use with AI agents.

## Prerequisites

- Python 3.11+
- Gainsight Customer Communities API credentials (OAuth2 client credentials)
- Docker (optional)

## Getting API Credentials

1. Log in to your community admin panel
2. Go to **Control → Integrations → API**
3. Create new API client credentials
4. Note your **Client ID**, **Client Secret**, and **Region** (EU or US)

For more detail, see the [API credentials guide](https://communities.gainsight.com/api-55/api-documentation-how-to-get-api-credentials-18403).

## Installation

### Local

```bash
git clone https://github.com/graemerycyk/gainsight-community-mcp.git
cd gainsight-community-mcp
pip install .
```

### Docker

```bash
docker build -t gainsight-community-mcp .
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GS_CC_CLIENT_ID` | Yes | — | OAuth2 client ID from your community admin panel |
| `GS_CC_CLIENT_SECRET` | Yes | — | OAuth2 client secret |
| `GS_CC_REGION` | No | `eu-west-1` | API region: `eu-west-1` or `us-west-2` |
| `GS_CC_COMMUNITY_URL` | No | — | Community front-end URL (e.g. `https://community.example.com`) |

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "gainsight-community": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "/path/to/gainsight-community-mcp",
      "env": {
        "GS_CC_CLIENT_ID": "your_client_id",
        "GS_CC_CLIENT_SECRET": "your_client_secret",
        "GS_CC_REGION": "eu-west-1",
        "GS_CC_COMMUNITY_URL": "https://community.example.com"
      }
    }
  }
}
```

### Claude Desktop (Docker)

```json
{
  "mcpServers": {
    "gainsight-community": {
      "command": "docker",
      "args": ["run", "-it", "--rm", "gainsight-community-mcp"],
      "env": {
        "GS_CC_CLIENT_ID": "your_client_id",
        "GS_CC_CLIENT_SECRET": "your_client_secret",
        "GS_CC_REGION": "eu-west-1",
        "GS_CC_COMMUNITY_URL": "https://community.example.com"
      }
    }
  }
}
```

### Region

| Your community URL contains | Region value |
|------------------------------|-------------|
| `api2-eu-west-1.insided.com` | `eu-west-1` |
| `api2-us-west-2.insided.com` | `us-west-2` |

Check **Control → Integrations → API** in your admin panel if unsure.

## Available Tools

### `search_community`

Search community content by keyword. Uses the same search algorithm as the community frontend and supports rich filtering.

```
"Search the community for posts about SSO integration"
"Find answered questions about API in the Developer category"
"Search for ideas tagged 'dark-mode'"
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string (required) | Search term |
| `category_ids` | string | Comma-separated category IDs to search within |
| `content_types` | string | Comma-separated content types, e.g. `"question,idea,article"` |
| `tags` | string | Comma-separated tags to filter results by |
| `moderator_tags` | string | Comma-separated moderator tags to filter results by |
| `has_answer` | bool | Set to `true` to only return questions that have answers |
| `page` | int | Page number (starts at 1) |

### `search_tags`

Search for tags by name. Returns matching tags with their IDs and usage counts. Useful for discovering exact tag names before filtering topics or search results.

```
"Search for tags matching 'api'"
"Find tags related to 'authentication'"
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search term to match against tag names |
| `page` | int | Page number (starts at 1) |

### `list_topics`

List community topics with optional filtering and sorting. When `content_type` is set, routes to the type-specific endpoint. For richer multi-type filtering, use the other parameters which query the unified endpoint.

```
"Show me all questions in the community"
"List topics tagged 'api' created after 2024-01-01"
"Show questions and ideas sorted by creation date"
```

| Param | Type | Description |
|-------|------|-------------|
| `content_type` | string | Route to a single type: `article`, `conversation`, `question`, `idea`, `productUpdate` |
| `category_ids` | string | Comma-separated category IDs (unified endpoint only) |
| `tags` | string | Comma-separated public tags |
| `moderator_tags` | string | Comma-separated moderator tags |
| `content_types` | string | Comma-separated content types, e.g. `"question,idea"` (unified endpoint only) |
| `sort` | string | Sort field: `"createdAt"`, `"lastActivity"` (descending) |
| `created_after` | string | ISO date — topics created on or after this date |
| `created_before` | string | ISO date — topics created on or before this date |
| `active_after` | string | ISO date — topics with activity on or after this date |
| `active_before` | string | ISO date — topics with activity on or before this date |
| `page` | int | Page number (starts at 1) |
| `page_size` | int | Results per page |

### `get_topic`

Retrieve full details for a specific topic, including body content and replies. Automatically resolves the content type.

| Param | Type | Description |
|-------|------|-------------|
| `topic_id` | int (required) | The numeric ID of the topic |

### `list_ideas`

List feature ideas/requests from the community.

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (starts at 1) |
| `page_size` | int | Results per page |

### `list_categories`

List all community categories with their IDs — useful for discovering community structure and getting IDs for `list_topics_by_category`.

### `list_tags`

List all public tags used in the community. Useful for discovering tags before filtering topics.

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (starts at 1) |
| `page_size` | int | Results per page |

### `get_category`

Get details for a single category by its ID.

| Param | Type | Description |
|-------|------|-------------|
| `category_id` | int (required) | The numeric ID of the category |

### `get_category_tree`

Get the full category hierarchy as a tree structure. Returns parent/child relationships between categories.

### `get_category_topic_counts`

Get the number of visible topics in each category. Useful for a quick community overview or identifying the most active areas.

### `list_topics_by_category`

List topics within a specific category with optional filtering.

| Param | Type | Description |
|-------|------|-------------|
| `category_id` | int (required) | The numeric ID of the category |
| `tags` | string | Comma-separated public tags |
| `moderator_tags` | string | Comma-separated moderator tags |
| `sort` | string | Sort field: `"createdAt"`, `"lastActivity"` (descending) |
| `created_after` | string | ISO date — topics created on or after this date |
| `created_before` | string | ISO date — topics created on or before this date |
| `active_after` | string | ISO date — topics with activity on or after this date |
| `active_before` | string | ISO date — topics with activity on or before this date |
| `page` | int | Page number (starts at 1) |
| `page_size` | int | Results per page |

### `list_idea_statuses`

List all idea statuses (e.g. "New", "Planned", "Shipped"). Useful for understanding the idea pipeline stages.

### `list_product_areas`

List all product areas defined in the community. Product areas are used to categorise ideas and product updates.

### `get_poll_results`

Get poll results for a topic that has a poll attached.

| Param | Type | Description |
|-------|------|-------------|
| `topic_id` | int (required) | The numeric ID of the topic |
| `content_type` | string (required) | The content type: `article`, `conversation`, `question`, `idea`, or `productUpdate` |

### `get_reply`

Fetch a single reply by its ID.

| Param | Type | Description |
|-------|------|-------------|
| `topic_id` | int (required) | The numeric ID of the parent topic |
| `reply_id` | int (required) | The numeric ID of the reply |
| `content_type` | string (required) | The content type: `article`, `conversation`, `question`, `idea`, or `productUpdate` |

### `get_community_info`

Get basic information about the connected community, including the front-end URL (if configured via `GS_CC_COMMUNITY_URL`) and the API region. Useful for constructing links to community content.

## Example Prompts

Once configured, you can ask your AI assistant things like:

**Search & browse:**
- *"Search our community for posts about dark mode"*
- *"Search for answered questions about SSO in the Developer category"*
- *"Find all ideas tagged 'dark-mode'"*
- *"What tags are related to 'authentication'?"*
- *"What are the top 10 most voted ideas?"*
- *"Show me all questions from last week that haven't been answered"*
- *"Get the full thread for topic 12345"*
- *"List all topics tagged 'api' sorted by creation date"*
- *"Show me questions and ideas created after 2025-01-01"*

**Explore community structure:**
- *"Show me the category tree"*
- *"Which categories have the most topics?"*
- *"List all categories in our community"*
- *"What tags are available?"*
- *"List all product areas"*

**Ideas & roadmap:**
- *"What idea statuses are configured?"*
- *"List all topics in the 'Feature Requests' category tagged 'api'"*
- *"Show me all ideas with the status 'Planned'"*

**Polls & replies:**
- *"Show the poll results for topic 789"*
- *"Get reply 456 from question 123"*

## Development

### Setup

```bash
git clone https://github.com/graemerycyk/gainsight-community-mcp.git
cd gainsight-community-mcp
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Project Structure

```
gainsight-community-mcp/
├── src/
│   ├── __init__.py
│   ├── __main__.py        # Entry point for python -m src
│   ├── client.py          # Async HTTP client with OAuth2 auth
│   └── server.py          # FastMCP server with tool definitions
├── tests/
│   ├── test_client.py     # API client tests (mocked HTTP via respx)
│   └── test_server.py     # MCP tool tests (mocked client)
├── .github/
│   └── workflows/
│       └── ci.yml         # GitHub Actions CI (Python 3.11–3.13)
├── pyproject.toml         # Project config, deps, build settings
├── Dockerfile
├── CLAUDE.md              # AI assistant development guidelines
├── AGENTS.md              # Architecture and agent integration docs
├── CONTRIBUTING.md        # Contribution guidelines
├── LICENSE                # MIT
└── README.md
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `mcp` | Model Context Protocol SDK (FastMCP server) |
| `httpx` | Async HTTP client for Gainsight API calls |
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `respx` | HTTP request mocking for tests |

## API Documentation

- [Community API Docs (EU)](https://api2-eu-west-1.insided.com/docs/) · [Search API (EU)](https://api2-eu-west-1.insided.com/docs/search/)
- [Community API Docs (US)](https://api2-us-west-2.insided.com/docs/) · [Search API (US)](https://api2-us-west-2.insided.com/docs/search/)
- [API Credentials Guide](https://communities.gainsight.com/api-55/api-documentation-how-to-get-api-credentials-18403)

## License

MIT — see [LICENSE](LICENSE) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Run the tests (`pytest`)
4. Commit your changes
5. Push to the branch
6. Open a Pull Request
