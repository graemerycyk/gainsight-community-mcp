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
| `list_topics` | User wants to browse or filter topics. Supports category, tag, date range, sort, and content type filtering. Set `content_type` for type-specific endpoints, or use `content_types`, `category_ids`, `tags`, `sort`, and date params for unified filtering. |
| `get_topic` | User wants the full content and replies of a specific topic (needs a topic ID from search/list results). Automatically resolves content type. |
| `list_ideas` | User wants to see feature requests or ideas. Dedicated shortcut for idea content. |
| `list_categories` | User wants to understand the community structure. Often a good first step. |
| `list_tags` | User wants to discover available tags for filtering. Useful before calling `list_topics` with tag filters. |
| `get_category` | User wants details about a specific category (needs a category ID). |
| `get_category_tree` | User wants to see the full category hierarchy with parent/child relationships. |
| `get_category_topic_counts` | User wants a quick overview of which categories are most active. |
| `list_topics_by_category` | User wants to browse topics within a specific category, with optional tag/date/sort filtering. |
| `list_idea_statuses` | User wants to understand the idea pipeline (e.g. "New", "Planned", "Shipped"). |
| `list_product_areas` | User wants to see the product area taxonomy used to categorise ideas and product updates. |
| `get_poll_results` | User wants to see poll votes on a specific topic. Requires topic ID and content type. |
| `get_reply` | User wants to read a specific reply. Requires topic ID, reply ID, and content type. |

## Typical Agent Workflows

### Discovery Flow
1. `list_categories` — understand community structure
2. `get_category_tree` — see the full hierarchy
3. `get_category_topic_counts` — identify active areas
4. `list_topics_by_category(category_id=...)` — browse a specific category
5. `get_topic(topic_id=...)` — read a specific thread with replies

### Search Flow
1. `search_community(query="...")` — find matching content
2. `get_topic(topic_id=...)` — drill into a specific result

### Ideas/Roadmap Flow
1. `list_idea_statuses()` — understand the pipeline stages
2. `list_product_areas()` — see the product taxonomy
3. `list_ideas()` — browse community ideas
4. `get_topic(topic_id=...)` — read full idea discussion with replies

### Filtered Browsing Flow
1. `list_tags()` — discover available tags
2. `list_topics(tags="api,sso", sort="createdAt")` — filter topics
3. `get_topic(topic_id=...)` — read a specific result

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

list_topics         →     Build params with     →  GET /v2/topics?tags=api&sort=createdAt
  tags="api"              date range serialisation     &createdAt={"from":"2024-01-01"}
  sort="createdAt"        (JSON objects for dates)
  created_after=
    "2024-01-01"
                    ←     Parse JSON response  ←   200 OK + {"result": [...]}
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
| idea | `GET /v2/ideas` | `GET /v2/ideas/{id}` | `GET /v2/ideas/{id}/replies` |
| productUpdate | `GET /v2/productUpdates` | `GET /v2/productUpdates/{id}` | `GET /v2/productUpdates/{id}/replies` |

Other endpoints:
- `/v2/categories`, `/v2/categories/{id}`, `/v2/category/getTree`, `/v2/categories/getVisibleTopicsCount`, `/v2/categories/{id}/topics`
- `/v2/tags`, `/v2/moderatorTags`
- `/v2/ideas/ideaStatuses`, `/v2/productAreas`
- `/v2/{type}s/{id}/poll`, `/v2/{type}s/{id}/replies/{replyId}`
- `/v2/topics/search`

Pagination: `pageSize` and `page` (1-indexed). Default page size is 25.

## Error Handling

Currently, HTTP errors propagate as `httpx.HTTPStatusError` exceptions. The MCP framework catches these and returns error responses to the agent. The `get_topic` tool handles "not found" gracefully by returning a structured error object. Future improvements could include:

- Retry logic for transient failures (429, 503)
- Graceful degradation when the API is unavailable

## Extending the Server

### Adding Write Operations

The Gainsight API supports write operations (creating content, replying, voting, moderation) via `scope=write`. To add write tools:

1. Update OAuth2 scope to `read write` in `client.py` (or make it configurable)
2. Add POST-based client methods for the desired endpoints
3. Add corresponding MCP tools with appropriate safety guardrails
4. Consider confirmation patterns for destructive actions

See the [API docs](https://api2-eu-west-1.insided.com/docs/) for available write endpoints.

### Adding Resources and Prompts

MCP also supports **resources** (read-only data) and **prompts** (templated interactions). Future versions could expose:

- **Resources**: Community stats, category tree snapshot, tag cloud
- **Prompts**: "Summarize top ideas this month", "Find unanswered questions"

## Multi-Agent Considerations

When multiple agents use this server concurrently:

- Each agent gets its own server process (launched by the host application)
- Each process manages its own OAuth2 token independently
- The Gainsight API has rate limits (approximately 300 requests/minute) — agents should paginate responsibly
- Token caching is per-process, so there's no shared state to coordinate
