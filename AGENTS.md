# AGENTS.md — Architecture & Agent Integration

This document describes how the MCP server works, how AI agents interact with it, and future directions.

## How It Works

```
┌─────────────┐     stdio (MCP)      ┌──────────────┐    HTTPS/OAuth2    ┌────────────────────┐
│  AI Agent   │ ◄──────────────────► │  MCP Server  │ ◄────────────────► │ Gainsight API      │
│  (Claude,   │   tool calls &       │  (FastMCP)   │   REST requests    │ (inSided)          │
│   Cursor)   │   results            │              │   + JSON responses │                    │
└─────────────┘                      └──────────────┘                    └────────────────────┘
```

1. The AI agent (e.g. Claude Desktop) launches the MCP server as a subprocess.
2. The server communicates over **stdio** using the MCP protocol.
3. When the agent invokes a tool, the server translates it into a Gainsight API call.
4. The server handles OAuth2 authentication transparently — the agent never sees credentials.

## Tool Descriptions for Agents

These descriptions help agents understand when to use each tool:

| Tool | When to Use |
|------|-------------|
| `search_community` | User wants to find content by keyword. Best for broad, text-based searches. |
| `list_topics` | User wants to browse or filter topics by type, category, tags, or date. Best for structured queries. |
| `get_topic` | User wants the full content and replies of a specific topic (needs a topic ID from search/list results). |
| `list_ideas` | User wants to see feature requests or ideas — shortcut for `list_topics` with `content_types=["idea"]`. |
| `list_categories` | User wants to understand the community structure, or needs category IDs for filtering. Often a good first step. |

## Typical Agent Workflows

### Discovery Flow
1. `list_categories` — understand community structure
2. `list_topics(category_ids=[...])` — browse a specific category
3. `get_topic(topic_id=...)` — read a specific thread

### Search Flow
1. `search_community(query="...")` — find matching content
2. `get_topic(topic_id=...)` — drill into a specific result

### Ideas/Roadmap Flow
1. `list_ideas(sort="voteCount")` — see most-voted ideas
2. `get_topic(topic_id=...)` — read full idea discussion

## Data Flow

```
Agent calls tool          Server processes          API request
─────────────────         ─────────────────         ─────────────────
search_community    →     Build query params   →   GET /api/v2/search?q=...
  query="SSO"             Strip None values
  content_types=          Join lists to CSV
    ["question"]          Ensure OAuth2 token

                    ←     Parse JSON response  ←   200 OK + JSON body
                          Return as string
```

## Authentication Architecture

```
First tool call:
  1. POST /oauth2/token  (client_id + client_secret)
  2. Receive access_token + expires_in
  3. Cache token, set expiry = now + expires_in - 60s

Subsequent calls:
  - If token not expired → reuse cached token
  - If token expired → repeat step 1-3
```

The 60-second buffer prevents requests from failing due to clock skew or network latency.

## Error Handling

Currently, HTTP errors propagate as `httpx.HTTPStatusError` exceptions. The MCP framework catches these and returns error responses to the agent. Future improvements could include:

- Structured error messages with community-specific context
- Retry logic for transient failures (429, 503)
- Graceful degradation when the API is unavailable

## Extending the Server

### Adding New Tools

The Gainsight Customer Communities API has additional endpoints not yet exposed:

| Potential Tool | API Endpoint | Use Case |
|----------------|-------------|----------|
| `get_user` | `GET /api/v2/users/{id}` | Look up community member profiles |
| `list_tags` | `GET /api/v2/tags` | Discover available tags for filtering |
| `get_category` | `GET /api/v2/categories/{id}` | Category details |
| `list_product_updates` | Topics with `content_types=productUpdate` | Product changelog |

### Adding Resources

MCP also supports **resources** (read-only data) and **prompts** (templated interactions). Future versions could expose:

- **Resources**: Community stats, category tree, tag cloud
- **Prompts**: "Summarize top ideas this month", "Find unanswered questions"

## Multi-Agent Considerations

When multiple agents use this server concurrently:

- Each agent gets its own server process (launched by the host application)
- Each process manages its own OAuth2 token independently
- The Gainsight API may have rate limits — agents should paginate responsibly
- Token caching is per-process, so there's no shared state to coordinate
