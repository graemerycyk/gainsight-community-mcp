# Gainsight Customer Communities MCP Server

A third-party [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for **Gainsight Customer Communities** (formerly inSided). Enables AI assistants like Claude, ChatGPT, and Cursor to search and retrieve community content through a standardised interface.

> **Note:** This is an independent, community-built integration — not officially supported by Gainsight.

## Features

- **Search** community content by keyword across all content types
- **List & filter topics** by type, category, tags, date range, and more
- **Retrieve full topic details** including replies
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
git clone https://github.com/YOUR_USERNAME/gainsight-community-mcp.git
cd gainsight-community-mcp
pip install .
```

### Docker

```bash
docker build -t gainsight-community-mcp .
```

## Configuration

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
"Find questions tagged 'api' created after 2025-01-01"
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string (required) | Search term |
| `content_types` | string[] | Filter: `article`, `conversation`, `question`, `idea`, `productUpdate` |
| `tags` | string | Comma-separated public tags |
| `sort` | string | `lastActivityAt`, `createdAt`, `likes`, `voteCount`, `replyCount` |
| `page` | int | Page number |
| `page_size` | int | Results per page (1–100) |

### `list_topics`

List and filter community topics with rich filtering options.

```
"Show me the most upvoted ideas from last month"
"List all articles in the API category"
```

| Param | Type | Description |
|-------|------|-------------|
| `content_types` | string[] | Filter by content type(s) |
| `category_ids` | string[] | Filter by category ID(s) |
| `tags` | string | Comma-separated tags |
| `moderator_tags` | string | Comma-separated moderator tags |
| `sort` | string | Sort field |
| `created_after` | string | ISO date, e.g. `"2025-01-01"` |
| `created_before` | string | ISO date |
| `page` / `page_size` | int | Pagination |

### `get_topic`

Retrieve full details for a specific topic, including body content and replies.

### `list_ideas`

List feature ideas/requests, sorted by votes or activity. Convenience wrapper that filters topics to ideas only.

### `list_categories`

List all community categories with their IDs — useful for filtering topics by category.

## Example Prompts

Once configured, you can ask your AI assistant things like:

- *"Search our community for posts about dark mode"*
- *"What are the top 10 most voted ideas?"*
- *"Show me all questions from last week that haven't been answered"*
- *"List all categories in our community"*
- *"Get the full thread for topic 12345"*

## API Documentation

- [Community API Docs (EU)](https://api2-eu-west-1.insided.com/docs/)
- [Community API Docs (US)](https://api2-us-west-2.insided.com/docs/)
- [API Credentials Guide](https://developer.insided.com/)

## License

MIT — see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
