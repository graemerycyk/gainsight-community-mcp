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
| `search_community` | User wants to find content by keyword. Best for broad, text-based searches across all content types. |
| `list_topics` | User wants to browse topics. Set `content_type` to filter to a specific type (question, article, idea, conversation, productUpdate). Without a type, returns all content. |
| `get_topic` | User wants the full content and replies of a specific topic (needs a topic ID from search/list results). Automatically resolves content type. |
| `list_ideas` | User wants to see feature requests or ideas. Dedicated shortcut for idea content. |
| `list_categories` | User wants to understand the community structure. Often a good first step. |

## Typical Agent Workflows

### Discovery Flow
1. `list_categories` — understand community structure
2. `list_topics(content_type="question")` — browse questions
3. `get_topic(topic_id=...)` — read a specific thread with replies

### Search Flow
1. `search_community(query="...")` — find matching content
2. `get_topic(topic_id=...)` — drill into a specific result

### Ideas/Roadmap Flow
1. `list_ideas()` — see community ideas
2. `get_topic(topic_id=...)` — read full idea discussion with replies

## Data Flow

```
Agent calls tool          Server processes          API request
─────────────────         ─────────────────         ─────────────────
search_community    →     Build query params   →   GET /v2/topics/search?q=...
  query="SSO"             Strip None values
                          Map pageSize param
                          Ensure OAuth2 token
                          (with scope=read)

                    ←     Parse JSON response  ←   200 OK + {"result": [...]}
                          Return as string

get_topic           →     1. Lookup: GET /v2/topics?id=42
  topic_id=42             2. Read contentType from result
                          3. Detail: GET /v2/questions/42
                          4. Replies: GET /v2/questions/42/replies
                    ←     Merge detail + replies, return JSON
```

## Authentication Architecture

```
First tool call:
  1. POST /oauth2/token  (client_id + client_secret + scope=read)
  2. Receive access_token + expires_in (7200s / 2 hours)
  3. Cache token, set expiry = now + expires_in - 60s

Subsequent calls:
  - If token not expired → reuse cached token
  - If token expired → repeat step 1-3
```

The 60-second buffer prevents requests from failing due to clock skew or network latency. The `scope=read` parameter is **required** — without it, the token is issued but API endpoints return 401.

## API Structure

The Gainsight Customer Communities API uses **content-type-specific endpoints**:

| Content Type | List Endpoint | Detail Endpoint | Replies Endpoint |
|-------------|---------------|-----------------|------------------|
| All types | `GET /v2/topics` | — | — |
| question | `GET /v2/questions` | `GET /v2/questions/{id}` | `GET /v2/questions/{id}/replies` |
| conversation | `GET /v2/conversations` | `GET /v2/conversations/{id}` | `GET /v2/conversations/{id}/replies` |
| article | `GET /v2/articles` | `GET /v2/articles/{id}` | `GET /v2/articles/{id}/replies` |
| idea | `GET /v2/ideas` | `GET /v2/ideas/{id}` | — |
| productUpdate | `GET /v2/productUpdates` | `GET /v2/productUpdates/{id}` | `GET /v2/productUpdates/{id}/replies` |

Other endpoints: `/v2/categories`, `/v2/tags`, `/v2/topics/search`

Pagination: `pageSize` and `page` (1-indexed). Default page size is 25.

## Error Handling

Currently, HTTP errors propagate as `httpx.HTTPStatusError` exceptions. The MCP framework catches these and returns error responses to the agent. The `get_topic` tool handles "not found" gracefully by returning a structured error object. Future improvements could include:

- Retry logic for transient failures (429, 503)
- Graceful degradation when the API is unavailable

## Extending the Server

### Adding New Tools

The Gainsight Customer Communities API has additional endpoints not yet exposed as MCP tools:

| Potential Tool | API Endpoint | Use Case |
|----------------|-------------|----------|
| `list_tags` | `GET /v2/tags` | Discover available tags (client method exists) |
| `list_product_updates` | `GET /v2/productUpdates` | Product changelog (client method exists) |
| `list_questions` | `GET /v2/questions` | Dedicated question listing |
| `list_conversations` | `GET /v2/conversations` | Dedicated conversation listing |
| `list_articles` | `GET /v2/articles` | Dedicated article listing |
| `get_user` | `GET /user` | Community member profiles |

### Adding Resources

MCP also supports **resources** (read-only data) and **prompts** (templated interactions). Future versions could expose:

- **Resources**: Community stats, category tree, tag cloud
- **Prompts**: "Summarize top ideas this month", "Find unanswered questions"

## Multi-Agent Considerations

When multiple agents use this server concurrently:

- Each agent gets its own server process (launched by the host application)
- Each process manages its own OAuth2 token independently
- The Gainsight API has rate limits (approximately 300 requests/minute) — agents should paginate responsibly
- Token caching is per-process, so there's no shared state to coordinate
