"""MCP server for Gainsight Customer Communities."""

from __future__ import annotations

import json
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from .client import GainsightClient

mcp = FastMCP(
    "Gainsight Customer Communities",
    instructions=(
        "Search and retrieve content from Gainsight Customer Communities "
        "(formerly inSided)."
    ),
)

_client: GainsightClient | None = None


def _get_client() -> GainsightClient:
    global _client
    if _client is None:
        _client = GainsightClient()
    return _client


def _clean(params: dict[str, Any]) -> dict[str, Any]:
    """Remove None values so they are not sent as query params."""
    return {k: v for k, v in params.items() if v is not None}


# ---------- Tools ----------


@mcp.tool()
async def search_community(
    query: str,
    category_ids: str | None = None,
    content_types: str | None = None,
    tags: str | None = None,
    moderator_tags: str | None = None,
    has_answer: bool | None = None,
    page: int | None = None,
) -> str:
    """Search community content by keyword. Uses the same search algorithm as the community frontend.

    Args:
        query: Search term (required).
        category_ids: Comma-separated category IDs to search within.
        content_types: Comma-separated content types to search (e.g. "question,idea,article").
        tags: Comma-separated tags to filter results by.
        moderator_tags: Comma-separated moderator tags to filter results by.
        has_answer: Set to true to only return questions that have answers.
        page: Page number for pagination (starts at 1).
    """
    client = _get_client()
    params = _clean(
        {
            "q": query,
            "categoryIds": category_ids,
            "contentTypes": content_types,
            "tags": tags,
            "moderatorTags": moderator_tags,
            "hasAnswer": has_answer,
            "page": page,
        }
    )
    result = await client.search(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def search_tags(
    query: str | None = None,
    page: int | None = None,
) -> str:
    """Search for tags by name. Returns matching tags with their IDs and usage counts.

    Useful for discovering the exact tag name before filtering topics or
    search results by tag.

    Args:
        query: Search term to match against tag names.
        page: Page number for pagination (starts at 1).
    """
    client = _get_client()
    params = _clean(
        {
            "q": query,
            "page": page,
        }
    )
    result = await client.search_tags(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_topics(
    content_type: str | None = None,
    category_ids: str | None = None,
    tags: str | None = None,
    moderator_tags: str | None = None,
    content_types: str | None = None,
    sort: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    active_after: str | None = None,
    active_before: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List community topics with optional filtering and sorting.

    When content_type is set, routes to the type-specific endpoint (e.g.
    /v2/questions). For richer filtering across all types use the other
    parameters which query the unified /v2/topics endpoint.

    Args:
        content_type: Route to a single type endpoint: article, conversation, question, idea, productUpdate.
        category_ids: Comma-separated category IDs to filter by (unified endpoint only).
        tags: Comma-separated public tags to filter by.
        moderator_tags: Comma-separated moderator tags to filter by.
        content_types: Comma-separated content types to filter by (unified endpoint only, e.g. "question,idea").
        sort: Sort field — e.g. "createdAt", "lastActivity" (descending order).
        created_after: ISO date string — only topics created on or after this date (e.g. "2024-01-01").
        created_before: ISO date string — only topics created on or before this date.
        active_after: ISO date string — only topics with activity on or after this date.
        active_before: ISO date string — only topics with activity on or before this date.
        page: Page number (starts at 1).
        page_size: Results per page.
    """
    client = _get_client()

    # Use type-specific endpoints when content_type is set
    if content_type:
        params = _clean({"page": page, "pageSize": page_size})
        if content_type == "question":
            result = await client.list_questions(params)
        elif content_type == "conversation":
            result = await client.list_conversations(params)
        elif content_type == "article":
            result = await client.list_articles(params)
        elif content_type == "idea":
            result = await client.list_ideas(params)
        elif content_type == "productUpdate":
            result = await client.list_product_updates(params)
        else:
            result = await client.list_topics(params)
        return json.dumps(result, indent=2)

    # Build unified /v2/topics params with full filtering support
    created_at = None
    if created_after or created_before:
        created_at = _clean({"from": created_after, "to": created_before})

    last_activity = None
    if active_after or active_before:
        last_activity = _clean({"from": active_after, "to": active_before})

    params = _clean(
        {
            "categoryIds": category_ids,
            "tags": tags,
            "moderatorTags": moderator_tags,
            "contentTypes": content_types,
            "sort": sort,
            "createdAt": json.dumps(created_at) if created_at else None,
            "lastActivity": json.dumps(last_activity) if last_activity else None,
            "page": page,
            "pageSize": page_size,
        }
    )
    result = await client.list_topics(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_topic(topic_id: int) -> str:
    """Retrieve full details for a specific topic, including body content and replies.

    Looks up the topic by ID to determine its content type, then fetches the
    full detail and replies from the type-specific endpoint.

    Args:
        topic_id: The numeric ID of the topic to retrieve.
    """
    client = _get_client()

    # Look up the topic to find its content type
    lookup = await client.get_topic_by_id(topic_id)
    results = lookup.get("result", [])
    if not results:
        return json.dumps({"error": f"Topic {topic_id} not found"})

    content_type = results[0]["contentType"]

    # Fetch full detail and replies using the type-specific endpoints
    topic = await client.get_topic_detail(content_type, topic_id)
    try:
        replies = await client.get_topic_replies(content_type, topic_id)
    except httpx.HTTPStatusError:
        replies = {"result": [], "_metadata": {"totalCount": 0}}
    topic["replies"] = replies

    return json.dumps(topic, indent=2)


@mcp.tool()
async def list_ideas(
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List feature ideas/requests from the community.

    Args:
        page: Page number (starts at 1).
        page_size: Results per page.
    """
    client = _get_client()
    params = _clean({"page": page, "pageSize": page_size})
    result = await client.list_ideas(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_categories() -> str:
    """List all community categories with their IDs.

    Useful for discovering community structure and getting category IDs
    for use with list_topics_by_category.
    """
    client = _get_client()
    result = await client.list_categories()
    return json.dumps(result, indent=2)


# ---------- New tools ----------


@mcp.tool()
async def list_tags(
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List all public tags used in the community.

    Useful for discovering available tags before filtering topics by tag.

    Args:
        page: Page number (starts at 1).
        page_size: Results per page.
    """
    client = _get_client()
    params = _clean({"page": page, "pageSize": page_size})
    result = await client.list_tags(params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_category(category_id: int) -> str:
    """Get details for a single category by its ID.

    Args:
        category_id: The numeric ID of the category.
    """
    client = _get_client()
    result = await client.get_category(category_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_category_tree() -> str:
    """Get the full category hierarchy as a tree structure.

    Returns parent/child relationships between categories.
    Useful for understanding the community's organisational structure.
    """
    client = _get_client()
    result = await client.get_category_tree()
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_category_topic_counts() -> str:
    """Get the number of visible topics in each category.

    Useful for a quick community overview or identifying the most active areas.
    """
    client = _get_client()
    result = await client.get_category_topic_counts()
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_topics_by_category(
    category_id: int,
    tags: str | None = None,
    moderator_tags: str | None = None,
    sort: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    active_after: str | None = None,
    active_before: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
) -> str:
    """List topics within a specific category.

    Use list_categories or get_category_tree first to find category IDs.

    Args:
        category_id: The numeric ID of the category (required).
        tags: Comma-separated public tags to filter by.
        moderator_tags: Comma-separated moderator tags to filter by.
        sort: Sort field — e.g. "createdAt", "lastActivity" (descending order).
        created_after: ISO date string — only topics created on or after this date.
        created_before: ISO date string — only topics created on or before this date.
        active_after: ISO date string — only topics with activity on or after this date.
        active_before: ISO date string — only topics with activity on or before this date.
        page: Page number (starts at 1).
        page_size: Results per page.
    """
    client = _get_client()

    created_at = None
    if created_after or created_before:
        created_at = _clean({"from": created_after, "to": created_before})

    last_activity = None
    if active_after or active_before:
        last_activity = _clean({"from": active_after, "to": active_before})

    params = _clean(
        {
            "tags": tags,
            "moderatorTags": moderator_tags,
            "sort": sort,
            "createdAt": json.dumps(created_at) if created_at else None,
            "lastActivity": json.dumps(last_activity) if last_activity else None,
            "page": page,
            "pageSize": page_size,
        }
    )
    result = await client.list_topics_by_category(category_id, params)
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_idea_statuses() -> str:
    """List all idea statuses (e.g. "New", "Planned", "Shipped").

    Useful for understanding the idea pipeline stages configured
    in the community.
    """
    client = _get_client()
    result = await client.list_idea_statuses()
    return json.dumps(result, indent=2)


@mcp.tool()
async def list_product_areas() -> str:
    """List all product areas defined in the community.

    Product areas are used to categorise ideas and product updates.
    """
    client = _get_client()
    result = await client.list_product_areas()
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_poll_results(topic_id: int, content_type: str) -> str:
    """Get poll results for a topic that has a poll attached.

    Args:
        topic_id: The numeric ID of the topic.
        content_type: The content type: article, conversation, question, idea, or productUpdate.
    """
    client = _get_client()
    result = await client.get_poll_results(content_type, topic_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_reply(
    topic_id: int,
    reply_id: int,
    content_type: str,
) -> str:
    """Fetch a single reply by its ID.

    Args:
        topic_id: The numeric ID of the parent topic.
        reply_id: The numeric ID of the reply.
        content_type: The content type: article, conversation, question, idea, or productUpdate.
    """
    client = _get_client()
    result = await client.get_reply(content_type, topic_id, reply_id)
    return json.dumps(result, indent=2)


@mcp.tool()
async def get_community_info() -> str:
    """Get basic information about the connected community.

    Returns the community front-end URL (if configured) and the API region.
    Useful for constructing links to community content or confirming which
    community the server is connected to.
    """
    client = _get_client()
    info: dict[str, Any] = {
        "region": client.region,
        "api_base_url": client.base_url,
    }
    if client.community_url:
        info["community_url"] = client.community_url
    return json.dumps(info, indent=2)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
