# Gainsight Customer Communities MCP Server

A third-party [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for **Gainsight Customer Communities** (formerly inSided). Enables AI assistants like Claude, ChatGPT, and Cursor to search and retrieve community content through a standardised interface.

> **Note:** This is an independent, community-built integration — not officially supported by Gainsight.

## Features

- **Search** community content by keyword across all content types
- **List & filter topics** by type, category, tags, date range, and more
- **Retrieve full topic details** including body content and replies
- **Browse ideas** and feature requests with vote counts
- **List categories** to discover community structure

## Prerequisites

- Python 3.11+
- Gainsight Customer Communities API credentials (OAuth2 client credentials)
- Docker (optional)

## Getting API Credentials

1. Log in to your community admin panel
2. Go to **Control → Integrations → API**
3. Create new API client credentials
4. Note your **Client ID**, **Client Secret**, and **Region** (EU or US)

For more detail, see the [API documentation](https://developer.insided.com/).

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
        "GS_CC_REGION": "eu-west-1"
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
        "GS_CC_REGION": "eu-west-1"
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

Search community content by keyword across all content types.

```
"Search the community for posts about SSO integration"
"Find posts mentioning API"
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string (required) | Search term |
| `page` | int | Page number (starts at 1) |
| `page_size` | int | Results per page |

### `list_topics`

List community topics, optionally filtered by content type.

```
"Show me all questions in the community"
"List all articles"
```

| Param | Type | Description |
|-------|------|-------------|
| `content_type` | string | Filter to: `article`, `conversation`, `question`, `idea`, `productUpdate` |
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

List all community categories with their IDs — useful for discovering community structure.

## Example Prompts

Once configured, you can ask your AI assistant things like:

- *"Search our community for posts about dark mode"*
- *"What are the top 10 most voted ideas?"*
- *"Show me all questions from last week that haven't been answered"*
- *"List all categories in our community"*
- *"Get the full thread for topic 12345"*

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

- [Community API Docs (EU)](https://api2-eu-west-1.insided.com/docs/)
- [Community API Docs (US)](https://api2-us-west-2.insided.com/docs/)
- [API Credentials Guide](https://developer.insided.com/)

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
